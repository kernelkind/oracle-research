import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from generation import collect, load_packages, prepare
from sse_multivector import codex_exec as runner


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False) + "\n", encoding="utf-8")


class GenerationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
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

    def test_subject_prompt_and_ordered_schema_match_frozen_reference_exactly(self):
        output = self.root / "subjects"
        report = prepare("subjects", self.source, output, start=1, stop=1)
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
        report = prepare("masks", self.source, output, start=1, stop=1)
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
        report = prepare("subjects", self.source, output, start=1, stop=13)
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
            prepare("subjects", self.source, output, start=1, stop=13)
        self.assertEqual(b"keep unchanged", (sentinel / "saved-result").read_bytes())

    def test_collect_preserves_saved_context_subject_receipt_and_original_without_judging(
        self,
    ):
        prepared = self.root / "subjects"
        report = prepare("subjects", self.source, prepared, start=1, stop=1)
        config_path = prepared / report["calls"][0]["config"]
        config = runner.PromptRunnerConfig.load(config_path)
        config.run_directory.mkdir()
        manifest = runner._build_prompt_manifest(config, "codex-cli 0.153.0")
        raw_manifest = runner._canonical_json_bytes(manifest)
        (config.run_directory / "manifest.json").write_bytes(raw_manifest)
        raw = '{"subjects":[{"context":"the auxiliary context","subject":"Rust."}]}'
        receipt = {
            "manifest_sha256": hashlib.sha256(raw_manifest).hexdigest(),
            "wrapper_sha256": manifest["wrapper_sha256"],
            "job_key": "prompt:" + config.prompts[0].prompt_id,
            "status": "succeeded",
            "attempt": 1,
            "stage": "prompt",
            "prompt_sha256": hashlib.sha256(
                config.prompts[0].text.encode()
            ).hexdigest(),
            "thread_id": "thread-one",
            "argv": ["codex", "exec", "--ephemeral"],
            "usage": {"input_tokens": 9, "output_tokens": 4},
            "response": raw,
            "final_output_raw": raw,
            "final_output_sha256": hashlib.sha256(raw.encode()).hexdigest(),
        }
        write(config.run_directory / "results.jsonl", receipt)
        write(
            config.run_directory / "output.json",
            {
                "schema_version": 1,
                "manifest_sha256": receipt["manifest_sha256"],
                "responses": [
                    {"prompt_id": config.prompts[0].prompt_id, "response": raw}
                ],
            },
        )
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
        self.assertEqual({"input_tokens": 9, "output_tokens": 4}, reviewed["usage"])
        with self.assertRaisesRegex(ValueError, "already exists"):
            collect(prepared, output)
        changed = copy.deepcopy(receipt)
        changed["manifest_sha256"] = "f" * 64
        write(config.run_directory / "results.jsonl", changed)
        with self.assertRaisesRegex(runner.RunnerError, "another manifest"):
            collect(prepared, self.root / "bad-collection")


if __name__ == "__main__":
    unittest.main()
