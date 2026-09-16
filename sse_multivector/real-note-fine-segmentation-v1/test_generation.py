import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from generation import collect, load_packages, prepare
from sse_multivector import extraction_pipeline as runner
from sse_multivector.test_extraction_pipeline import FAKE_RUNNER


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False) + "\n", encoding="utf-8")


class GenerationTests(unittest.TestCase):
    def test_saved_codex_run_remains_collectable_without_credentials_or_execution(self):
        source = Path(__file__).resolve().parent / "subjects-001-010"
        original = (source / "N001-AS/run/results.jsonl").read_bytes()
        self.auth_file.unlink()
        review = collect(source, self.root / "historical-review")
        self.assertEqual(10, len(review["notes"]))
        first = review["notes"][0]["outputs"][0]
        self.assertIn("codex_version", first["receipt"])
        self.assertIn("thread_id", first["receipt"])
        self.assertNotIn("model_result", first["receipt"])
        self.assertEqual(original, (source / "N001-AS/run/results.jsonl").read_bytes())
        self.assertFalse((self.root / "calls.json").exists())

    def test_native_prepare_execute_collect_keeps_frozen_inputs_and_real_receipt(self):
        auth = self.root / "auth.json"
        auth.write_text("fixture")
        auth.chmod(0o600)
        binary = self.root / "model-runner"
        binary.write_text(FAKE_RUNNER)
        binary.chmod(0o755)
        prepared = self.root / "native"
        report = prepare(
            "subjects", self.source, prepared, auth_file=auth, runner_binary=binary
        )
        raw = '{"subjects":[{"context":"a context","subject":"Rust."}]}'
        jobs = json.loads((prepared / report["job_batches"][0]).read_text())["jobs"]
        environment = {
            **os.environ,
            "FAKE_RUNNER_LOG": str(self.root / "calls.json"),
            "FAKE_RUNNER_RESULT_OVERRIDE": json.dumps(
                {"raw_text": raw, "output": json.loads(raw)}
            ),
        }
        result = subprocess.run(
            jobs[0]["command"],
            env=environment,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        review = collect(prepared, self.root / "native-review")
        item = review["notes"][0]["outputs"][0]
        self.assertEqual(item["raw_response"], raw)
        self.assertEqual(item["receipt"]["model_result"]["raw_text"], raw)
        self.assertEqual(item["receipt"]["provider"], "openai-codex")
        self.assertNotIn("thread_id", item["receipt"])
        self.assertEqual(review["notes"][0]["text"], self.document["notes"][0]["text"])

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.auth_file = self.root / "auth.json"
        self.auth_file.write_text("fixture")
        self.auth_file.chmod(0o600)
        self.fake_runner = self.root / "fake-model"
        self.fake_runner.write_text(FAKE_RUNNER)
        self.fake_runner.chmod(0o755)
        self.source = self.root / "notes.json"
        self.document = {
            "schema_version": 1,
            "notes": [
                {
                    "note_id": "a" * 64,
                    "text": "☕ Rust nostr:npub1"
                    + "q" * 63
                    + " {SUBJECT}\nhttps://example.com/full",
                    "provenance": {"source": "saved-note"},
                    "subjects": [
                        {
                            "id": "subject-one",
                            "context": "AUXILIARY_SECRET",
                            "subject": "Rust.",
                            "judgment": "accepted",
                        },
                        {
                            "id": "subject-two",
                            "context": "OTHER_CONTEXT",
                            "subject": "SIBLING_SECRET",
                            "judgment": "unresolved",
                        },
                    ],
                }
            ],
        }
        write(self.source, self.document)

    def prepare(self, *args, **kwargs):
        return prepare(
            *args, auth_file=self.auth_file, runner_binary=self.fake_runner, **kwargs
        )

    def test_subject_prompt_and_ordered_schema_match_frozen_reference_exactly(self):
        output = self.root / "subjects"
        report = self.prepare("subjects", self.source, output, start=1, stop=1)
        config_path = output / report["calls"][0]["config"]
        config = runner.PromptRunnerConfig.load(config_path)
        package = load_packages()
        expected = runner._render_subject_prompt(
            package["subject_prompt"].strip(),
            runner.Note("a" * 64, self.document["notes"][0]["text"]),
        )
        self.assertEqual(expected, config.prompts[0].text)
        self.assertNotIn("nostr:npub1", config.prompts[0].text)
        self.assertIn("https://example.com/full", config.prompts[0].text)
        self.assertEqual(
            "3e66f7a7d499bbb76ce8bcd2797f74a25d403f658341721b9631e235c3885c51",
            hashlib.sha256(
                runner._ordered_json_bytes(config.output_schema)
            ).hexdigest(),
        )
        reference = json.loads(
            (
                package["subject_root"]
                / "../asv6.23-validation-v1/final/H51-t1/config.json"
            ).read_text()
        )
        notes = json.loads(
            (
                package["mask_root"] / "subject-deletion-v1/final/batch-a/input.json"
            ).read_text()
        )
        self.assertEqual(
            reference["prompts"][0]["text"],
            runner._render_subject_prompt(
                package["subject_prompt"].strip(),
                runner.Note("ref", notes["notes"][1]["text"]),
            ),
        )

    def test_mask_uses_complete_original_and_one_unchanged_reviewed_subject(self):
        output = self.root / "masks"
        report = self.prepare("masks", self.source, output, start=1, stop=1)
        self.assertEqual(1, len(report["calls"]))
        config = runner.PromptRunnerConfig.load(output / report["calls"][0]["config"])
        expected = (
            load_packages()["mask_prompt"].split("{POST}")[0]
            + self.document["notes"][0]["text"]
            + "\n</post>\n\n<subject>\nRust.\n</subject>\n"
        )
        self.assertEqual(expected, config.prompts[0].text)
        self.assertIsNone(config.output_schema)
        self.assertIn("nostr:npub1", config.prompts[0].text)
        self.assertIn("{SUBJECT}", config.prompts[0].text)
        self.assertNotIn("AUXILIARY_SECRET", config.prompts[0].text)
        self.assertNotIn("SIBLING_SECRET", config.prompts[0].text)
        self.assertEqual(1, len(report["excluded"]))

    def test_unique_per_call_context_and_small_batches_refuse_to_overwrite(self):
        self.document["notes"] = [
            {"note_id": f"{index:064x}", "text": f"Note {index}."}
            for index in range(1, 14)
        ]
        write(self.source, self.document)
        output = self.root / "subjects"
        report = self.prepare("subjects", self.source, output, start=1, stop=13)
        jobs = [
            json.loads((output / name).read_text())["jobs"]
            for name in report["job_batches"]
        ]
        self.assertEqual([12, 1], [len(batch) for batch in jobs])
        configs = [
            runner.PromptRunnerConfig.load(output / call["config"])
            for call in report["calls"]
        ]
        self.assertEqual(13, len({config.run_directory for config in configs}))
        self.assertTrue(all(len(config.prompts) == 1 for config in configs))
        self.assertTrue(
            all(job["command"][2] == "prompt" for batch in jobs for job in batch)
        )
        sentinel = configs[0].run_directory
        sentinel.mkdir()
        (sentinel / "saved-result").write_bytes(b"keep unchanged")
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.prepare("subjects", self.source, output, start=1, stop=13)
        self.assertEqual(b"keep unchanged", (sentinel / "saved-result").read_bytes())

    def test_collect_preserves_saved_context_subject_receipt_and_original_without_judging(
        self,
    ):
        prepared = self.root / "subjects"
        report = self.prepare("subjects", self.source, prepared, start=1, stop=1)
        config_path = prepared / report["calls"][0]["config"]
        config = runner.PromptRunnerConfig.load(config_path)
        raw = '{"subjects":[{"context":"the auxiliary context","subject":"Rust."}]}'
        usage = {"input": 9, "output": 4, "cacheRead": 0, "cacheWrite": 0}
        environment = {
            **os.environ,
            "FAKE_RUNNER_LOG": str(self.root / "calls.json"),
            "FAKE_RUNNER_RESULT_OVERRIDE": json.dumps(
                {"raw_text": raw, "output": json.loads(raw), "usage": usage}
            ),
        }
        completed = subprocess.run(
            [
                sys.executable,
                "-B",
                str(Path(runner.__file__)),
                "prompt",
                str(config_path),
            ],
            env=environment,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        manifest = json.loads((config.run_directory / "manifest.json").read_text())
        receipt = json.loads((config.run_directory / "results.jsonl").read_text())
        output = self.root / "collected"
        collect(prepared, output)
        reviewed = json.loads((output / "review.json").read_text())
        note = reviewed["notes"][0]
        self.assertEqual(self.document["notes"][0]["text"], note["text"])
        result = note["outputs"][0]
        self.assertEqual(raw, result["raw_response"])
        self.assertEqual(
            [{"context": "the auxiliary context", "subject": "Rust."}],
            result["parsed_response"]["subjects"],
        )
        self.assertEqual(receipt, result["receipt"])
        self.assertEqual(manifest["isolation"], result["isolation"])
        self.assertEqual(manifest["config_sha256"], result["config_sha256"])
        self.assertNotIn("judgment", result)
        self.assertEqual(usage, reviewed["usage"])
        with self.assertRaisesRegex(ValueError, "already exists"):
            collect(prepared, output)
        changed = copy.deepcopy(receipt)
        changed["manifest_sha256"] = "f" * 64
        write(config.run_directory / "results.jsonl", changed)
        with self.assertRaisesRegex(runner.RunnerError, "another manifest"):
            collect(prepared, self.root / "bad-collection")


if __name__ == "__main__":
    unittest.main()
