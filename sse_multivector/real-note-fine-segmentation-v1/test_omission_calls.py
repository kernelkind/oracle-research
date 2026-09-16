import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import omission_calls as calls
from generation import read, sha, write
from sse_multivector import extraction_pipeline as runner
from sse_multivector.test_extraction_pipeline import FAKE_RUNNER


E = Path(__file__).resolve().parent


class OmissionCallsTests(unittest.TestCase):
    def test_saved_codex_omission_calls_keep_legacy_provenance_without_execution(self):
        manifest, saved = calls.saved_calls(E / "omission-audit-v1/text", "text")
        self.assertEqual(4, len(saved))
        self.assertEqual("codex-cli 0.153.0", manifest["codex_version"])
        self.assertEqual(4, len({call["thread_id"] for call in saved}))
        self.assertTrue(all("stdout_jsonl" in call["receipt"] for call in saved))
        self.assertFalse((self.root / "calls.json").exists())

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.auth_file = self.root / "auth.json"
        self.auth_file.write_text("fixture")
        self.auth_file.chmod(0o600)
        self.fake_runner = self.root / "fake-model"
        self.fake_runner.write_text(FAKE_RUNNER)
        self.fake_runner.chmod(0o755)
        self.runtime = {"auth_file": self.auth_file, "runner_binary": self.fake_runner}
        reference = self.root / "subjects-001-010/N001-AS/config.json"
        reference.parent.mkdir(parents=True)
        reference.write_bytes((E / "subjects-001-010/N001-AS/config.json").read_bytes())
        vectors = []
        for index in range(1, 9):
            note = (index - 1) // 2 + 1
            vectors.append(
                {
                    "short_id": f"V{index:03d}",
                    "vector_id": f"{index:064x}",
                    "note_id": f"{note:064x}",
                    "note_short_id": f"N{note:03d}",
                    "fragments": [f"☕ mask {index}", "milk"],
                    "subject": "SECRET_SUBJECT",
                    "reviewed_subject": {"context": "SECRET_CONTEXT"},
                }
            )
        (self.root / "vectors").mkdir()
        write(
            self.root / "vectors/vector-map.json",
            {"schema_version": 1, "vector_count": 8, "vectors": vectors},
        )
        write(
            self.root / "vectors/manifest.json",
            {
                "files": {
                    "vector-map.json": {
                        "sha256": sha(self.root / "vectors/vector-map.json")
                    }
                }
            },
        )
        baseline = self.root / "hdbscan-baseline/review/review.json"
        baseline.parent.mkdir(parents=True)
        write(
            baseline,
            {
                "schema_version": 3,
                "packets": [
                    {
                        "packet": "S001",
                        "instances": [
                            self.instance(vectors[0]),
                            self.instance(vectors[2]),
                        ],
                    },
                    {
                        "packet": "S002",
                        "instances": [
                            self.instance(vectors[4]),
                            self.instance(vectors[5]),
                        ],
                    },
                ],
            },
        )
        write(
            baseline.parent / "manifest.json",
            {"files": {"review.json": {"sha256": sha(baseline)}}},
        )

    @staticmethod
    def instance(vector):
        return {
            "instance": vector["short_id"],
            "vector_id": vector["vector_id"],
            "note_id": vector["note_id"],
            "text": "☕ milk SECRET_FULL_NOTE",
            "byte_spans": [[0, 3], [4, 8]],
        }

    def prepare_text(self):
        destination = self.root / "text"
        return destination, calls.prepare_text(self.root, destination, **self.runtime)

    def good_text_responses(self, manifest):
        catalog = {row["id"]: row for row in manifest["catalog"]}
        responses = {}
        for call in manifest["calls"]:
            rows = []
            for target in call["targets"]:
                partner = "V004" if target == "V002" else "V002"
                if catalog[partner]["note_id"] == catalog[target]["note_id"]:
                    partner = "V005"
                rows.append({"target": target, "partners": [partner]})
            responses[call["id"]] = rows
        return responses

    def save_responses(self, prepared, manifest, responses, duplicate_response=False):
        for index, call in enumerate(manifest["calls"]):
            config_path = prepared / call["config"]
            config = runner.PromptRunnerConfig.load(config_path)
            if config.run_directory.exists():
                shutil.rmtree(config.run_directory)
            raw = json.dumps(responses[call["id"]], ensure_ascii=False)
            response_id = "response-0" if duplicate_response else f"response-{index}"
            environment = {
                **os.environ,
                "FAKE_RUNNER_LOG": str(self.root / "calls.json"),
                "FAKE_RUNNER_RESULT_OVERRIDE": json.dumps(
                    {"raw_text": raw, "output": raw, "response_id": response_id}
                ),
            }
            result = subprocess.run(
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
            self.assertEqual(result.returncode, 0, result.stderr)

    def judge_review(self):
        source = self.root / "sample.json"
        instructions = read(E / "hdbscan-baseline/review/review.json")["instructions"]
        packets = []
        for index in range(128):
            instances = [
                {
                    "instance": f"V{offset:03d}",
                    "vector_id": f"{offset:064x}",
                    "note_id": f"{offset:064x}",
                    "text": "☕ milk SECRET_FULL_NOTE",
                    "byte_spans": [[0, 3], [4, 8]],
                }
                for offset in (1, index + 2)
            ]
            packets.append({"packet": f"S{index:010x}", "instances": instances})
        write(
            source,
            {
                "schema_version": 3,
                "review_set": "fixture",
                "instructions": instructions,
                "packets": packets,
                "scores": "SECRET_SCORE",
                "method": "SECRET_METHOD",
            },
        )
        return source

    def test_text_blinding_four_disjoint_fresh_calls_and_no_overwrite(self):
        prepared, manifest = self.prepare_text()
        self.assertEqual(4, len(manifest["calls"]))
        targets = [target for call in manifest["calls"] for target in call["targets"]]
        self.assertEqual(
            ["V002", "V004", "V005", "V006", "V007", "V008"], sorted(targets)
        )
        self.assertEqual(len(targets), len(set(targets)))
        self.assertEqual(
            [1, 3],
            [len(read(prepared / name)["jobs"]) for name in manifest["job_batches"]],
        )
        configs = [
            runner.PromptRunnerConfig.load(prepared / call["config"])
            for call in manifest["calls"]
        ]
        self.assertEqual(4, len({config.run_directory for config in configs}))
        for call, config in zip(manifest["calls"], configs):
            self.assertIsNone(config.output_schema)
            self.assertEqual(
                ("gpt-6-astra", "low"), (config.model, config.reasoning_effort)
            )
            prompt = config.prompts[0].text
            self.assertEqual(prompt, (prepared / call["prompt"]).read_text())
            self.assertIn("V001 N001 ⟦☕ mask 1⟧ ⟦milk⟧", prompt)
            self.assertIn("V008 N004 ⟦☕ mask 8⟧ ⟦milk⟧", prompt)
            self.assertNotIn("SECRET_", prompt)
            self.assertNotIn("baseline", prompt)
            self.assertNotIn("cosine", prompt)
        with self.assertRaisesRegex(ValueError, "already exists"):
            calls.prepare_text(self.root, prepared, **self.runtime)

    def test_text_collect_complete_coverage_dedup_and_raw_provenance(self):
        prepared, manifest = self.prepare_text()
        responses = self.good_text_responses(manifest)
        self.save_responses(prepared, manifest, responses)
        output = self.root / "pairs.json"
        result = calls.collect_text(prepared, output)
        self.assertEqual(result, read(output))
        self.assertEqual(len(result), len({tuple(pair) for pair in result}))
        self.assertEqual(1, result.count(["V002", "V004"]))
        provenance = read(output.with_suffix(".provenance.json"))
        self.assertEqual(4, len(provenance["calls"]))
        self.assertTrue(all(row["raw_response"] for row in provenance["calls"]))
        self.assertEqual(4, len({row["response_id"] for row in provenance["calls"]}))
        with self.assertRaisesRegex(ValueError, "already exists"):
            calls.collect_text(prepared, output)

    def test_text_collect_rejects_bad_coverage_ids_and_note_constraints(self):
        prepared, manifest = self.prepare_text()
        good = self.good_text_responses(manifest)
        first = manifest["calls"][0]["id"]
        changes = [
            [],
            good[first] + [good[first][0]],
            [{"target": "V999", "partners": []}],
            [{"target": row["target"], "partners": ["V999"]} for row in good[first]],
            [
                {"target": row["target"], "partners": ["V003", "V005", "V007", "V008"]}
                for row in good[first]
            ],
        ]
        for index, changed in enumerate(changes):
            with self.subTest(index=index):
                responses = copy.deepcopy(good)
                responses[first] = changed
                self.save_responses(prepared, manifest, responses)
                destination = self.root / f"bad-{index}.json"
                with self.assertRaises(ValueError):
                    calls.collect_text(prepared, destination)
                self.assertFalse(destination.exists())

    def test_receipt_prompt_hash_and_response_ids_are_bound(self):
        prepared, manifest = self.prepare_text()
        responses = self.good_text_responses(manifest)
        self.save_responses(prepared, manifest, responses, duplicate_response=True)
        with self.assertRaisesRegex(ValueError, "response ID"):
            calls.collect_text(prepared, self.root / "duplicate.json")
        self.save_responses(prepared, manifest, responses)
        receipt_path = prepared / manifest["calls"][0]["id"] / "run/results.jsonl"
        receipt = read(receipt_path)
        receipt["prompt_sha256"] = "0" * 64
        receipt_path.write_text(json.dumps(receipt) + "\n")
        with self.assertRaisesRegex(ValueError, "receipt"):
            calls.collect_text(prepared, self.root / "wrong-prompt.json")

    def test_changed_baseline_membership_fails_declared_source_hash(self):
        baseline = self.root / "hdbscan-baseline/review/review.json"
        document = read(baseline)
        document["packets"] = []
        baseline.write_text(json.dumps(document))
        with self.assertRaisesRegex(ValueError, "baseline.*hash"):
            calls.prepare_text(self.root, self.root / "changed", **self.runtime)
        self.assertFalse((self.root / "changed").exists())

    def test_text_collect_filters_ineligible_proposals_preserving_raw(self):
        prepared, manifest = self.prepare_text()
        good = self.good_text_responses(manifest)
        first = manifest["calls"][0]["id"]
        cases = [
            (["V002", "V001", "V003"], ["self_partner", "same_note"], []),
            (
                ["V003", "V003", "V004"],
                [],
                ["duplicate_partner", "repeated_partner_note"],
            ),
        ]
        for index, (partners, reasons, violations) in enumerate(cases):
            with self.subTest(index=index):
                responses = copy.deepcopy(good)
                responses[first][0]["partners"] = partners
                self.save_responses(prepared, manifest, responses)
                output = self.root / f"filtered-{index}.json"
                pairs = calls.collect_text(prepared, output)
                self.assertIn(["V002", "V003"], pairs)
                self.assertNotIn(["V001", "V002"], pairs)
                self.assertNotIn(["V002", "V002"], pairs)
                provenance = read(output.with_suffix(".provenance.json"))
                self.assertEqual(
                    reasons, [row["reason"] for row in provenance["rejected_proposals"]]
                )
                self.assertEqual(
                    violations,
                    [row["reason"] for row in provenance["instruction_violations"]],
                )
                raw = provenance["calls"][0]["raw_response"]
                self.assertEqual(partners, json.loads(raw)[0]["partners"])

    def test_eligible_repeated_note_proposals_stay_in_the_pool(self):
        prepared, manifest = self.prepare_text()
        responses = {
            call["id"]: [
                {"target": target, "partners": []} for target in call["targets"]
            ]
            for call in manifest["calls"]
        }
        first = manifest["calls"][0]["id"]
        responses[first][0]["partners"] = ["V003", "V004", "V003"]
        self.save_responses(prepared, manifest, responses)
        output = self.root / "retained.json"
        self.assertEqual(
            [["V002", "V003"], ["V002", "V004"]], calls.collect_text(prepared, output)
        )
        provenance = read(output.with_suffix(".provenance.json"))
        self.assertEqual([], provenance["rejected_proposals"])
        self.assertEqual(
            ["repeated_partner_note", "duplicate_partner"],
            [row["reason"] for row in provenance["instruction_violations"]],
        )

    def test_judge_prompt_names_each_allowed_verdict(self):
        source = self.judge_review()
        prepared = self.root / "labels"
        manifest = calls.prepare_judges(
            source, prepared, root=self.root, **self.runtime
        )
        prompt = (prepared / manifest["calls"][0]["prompt"]).read_text()
        for verdict in ("valid", "invalid", "uncertain"):
            self.assertIn(
                verdict + ": " + read(source)["instructions"][verdict], prompt
            )

    def test_two_judge_rounds_blinded_coverage_and_batch_gate(self):
        source = self.judge_review()
        prepared = self.root / "judge"
        manifest = calls.prepare_judges(
            source, prepared, root=self.root, **self.runtime
        )
        self.assertEqual(16, len(manifest["calls"]))
        self.assertEqual(
            [2, 7, 7],
            [len(read(prepared / name)["jobs"]) for name in manifest["job_batches"]],
        )
        for round_id in ("A", "B"):
            ids = [
                pid
                for call in manifest["calls"]
                if call["round"] == round_id
                for pid in call["packets"]
            ]
            self.assertEqual(128, len(set(ids)))
        rounds = [
            [call for call in manifest["calls"] if call["round"] == r]
            for r in ("A", "B")
        ]
        self.assertEqual(
            rounds[0][0]["packets"], list(reversed(rounds[1][0]["packets"]))
        )
        for call in manifest["calls"]:
            prompt = (prepared / call["prompt"]).read_text()
            self.assertNotIn("SECRET_", prompt)
            self.assertNotIn("N001", prompt)
            self.assertIn("V001 ⟦☕⟧ ⟦milk⟧", prompt)
            for instruction in read(source)["instructions"].values():
                self.assertIn(instruction, prompt)
        responses = {
            call["id"]: [
                {
                    "packet": packet,
                    "verdict": "uncertain",
                    "comment": "Selected fragments.",
                }
                for packet in call["packets"]
            ]
            for call in manifest["calls"]
        }
        self.save_responses(prepared, manifest, responses)
        output = self.root / "judgments.json"
        result = calls.collect_judgments(prepared, output)
        self.assertEqual([128, 128], [len(r["judgments"]) for r in result["rounds"]])
        self.assertEqual(16, len({row["response_id"] for row in result["calls"]}))
        self.assertNotIn("winner", result)
        bad = copy.deepcopy(responses)
        bad[manifest["calls"][0]["id"]][0]["verdict"] = "accepted"
        self.save_responses(prepared, manifest, bad)
        with self.assertRaisesRegex(ValueError, "verdict"):
            calls.collect_judgments(prepared, self.root / "bad-judge.json")


if __name__ == "__main__":
    unittest.main()
