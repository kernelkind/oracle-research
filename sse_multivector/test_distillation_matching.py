"""Matching-only controls through the production experiment workflow."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from sse_multivector import experiment_inputs as inputs
from sse_multivector import distillation_matching as matching
from sse_multivector.test_extraction_pipeline import FAKE_RUNNER


ROOT = Path(__file__).resolve().parent


class DistillationMatchingTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / "source.json"
        reference = ROOT / "distillation-review-v1/qualification-source.json"
        self.source = dict(schema_version=1,
            review_source=dict(path=str(reference),
                              sha256=hashlib.sha256(reference.read_bytes()).hexdigest()),
            cases=[dict(id="M01", case="Q09", student_number="1.1.1.1", replacements=[],
                        expected_teacher_number="1.1.1.1", expected_reason="Length and identity retained.",
                        partition="development"),
                   dict(id="M02", case="Q10", student_number="1.2.1.1", replacements=[],
                        expected_teacher_number=None, expected_reason="Negation removed.",
                        partition="development")])
        self.write()

    def write(self):
        self.path.write_text(json.dumps(self.source))

    def prepare(self, select=None):
        dataset = dict(adapter="distillation_matching")
        if select is not None:
            dataset["select"] = select
        return inputs.prepare_file(dataset, self.path, "DSMv1\n{MATCH_INPUT}")

    def validate(self, case, value):
        return inputs.validate(dict(adapter="distillation_matching"), case, json.dumps(value), None)

    def test_one_subject_fixed_catalog_and_gold_kept_outside_prompt(self):
        cases, protected, preparation = self.prepare()
        payload = json.loads(cases[0]["inputs"]["MATCH_INPUT"])
        self.assertEqual(set(payload), {"teacher_subjects", "student_subject"})
        self.assertEqual(payload["student_subject"], "Cable A, two metres long")
        self.assertEqual(len(payload["teacher_subjects"]), 10)
        self.assertEqual(payload["teacher_subjects"][3], dict(id="T04", subject="2 m cable A"))
        self.assertEqual(payload["teacher_subjects"],
                         json.loads(cases[1]["inputs"]["MATCH_INPUT"])["teacher_subjects"])
        self.assertEqual(cases[0]["evidence"]["expected_teacher_id"], "T04")
        self.assertIsNone(cases[1]["evidence"]["expected_teacher_id"])
        self.assertEqual(len(cases[0]["evidence"]["teacher_numbers"]["T10"]), 4)
        for forbidden in ("expected", "context", "1.1.1.1", "<post>", "partition"):
            self.assertNotIn(forbidden, cases[0]["prompt"])
        self.assertIn(str(self.path.resolve()), protected)
        self.assertEqual(preparation["qualification_case_ids"], ["M01", "M02"])

    def test_semantic_errors_are_valid_reports_with_separate_error_types(self):
        positive, negative = self.prepare()[0]
        self.assertTrue(self.validate(positive, dict(teacher_id="T04", reason="Same length and cable."))["qualification"]["passed"])
        for case, teacher_id, error in ((positive, None, "missed_match"),
                (positive, "T06", "wrong_match"), (negative, "T10", "false_match")):
            result = self.validate(case, dict(teacher_id=teacher_id, reason="A semantic judgment."))
            self.assertEqual(result["status"], "valid")
            self.assertFalse(result["qualification"]["passed"])
            self.assertEqual(result["qualification"]["error"], error)
        self.assertTrue(self.validate(negative, dict(teacher_id=None, reason="Polarity differs."))["qualification"]["passed"])

    def test_unknown_ids_duplicate_fields_and_malformed_reports_are_rejected(self):
        case = self.prepare()[0][0]
        for value in (dict(teacher_id="T99", reason="Unknown."),
                      dict(teacher_id=["T04"], reason="Wrong shape."),
                      dict(teacher_id="T04", reason=" "), dict(teacher_id="T04"),
                      dict(teacher_id="T04", reason="OK", extra=True)):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.validate(case, value)
        with self.assertRaises(ValueError):
            inputs.validate(dict(adapter="distillation_matching"), case,
                            '{"teacher_id":null,"teacher_id":"T04","reason":"Duplicate."}', None)

    def test_source_binding_selection_and_exact_match_exclusion(self):
        self.assertEqual([c["id"] for c in self.prepare(["M02"])[0]], ["M02"])
        for selected in (["unknown"], ["M01", "M01"]):
            with self.assertRaises(ValueError):
                self.prepare(selected)
        original = copy.deepcopy(self.source)
        self.source["review_source"]["sha256"] = "0" * 64
        self.write()
        with self.assertRaisesRegex(ValueError, "hash differs"):
            self.prepare()
        self.source = original
        self.source["cases"][0]["case"] = "Q06"
        self.write()
        with self.assertRaisesRegex(ValueError, "exact match"):
            self.prepare()

    def test_reference_notes_cannot_cross_control_partitions(self):
        self.source["cases"][1]["partition"] = "confirmation"
        self.write()
        with self.assertRaisesRegex(ValueError, "partition"):
            self.prepare(["M01"])

    def test_large_reference_never_reads_provisional_model_groups(self):
        self.source["cases"] = [dict(id="L01", case="Q21", student_number="1.1.1",
            replacements=[], expected_teacher_number="1.1.1", expected_reason="Faithful paraphrase.",
            partition="development")]
        self.write()
        cases, protected, _ = self.prepare()
        self.assertEqual(len(json.loads(cases[0]["inputs"]["MATCH_INPUT"])["teacher_subjects"]), 66)
        self.assertFalse(any("qualification-compatible-schema" in path for path in protected))

    def test_cli_preparation_and_native_reporting_without_real_models(self):
        root = self.path.parent
        runner = root / "fake-runner"
        runner.write_text(FAKE_RUNNER.replace('if prompt.startswith("GENERIC PROMPT"):',
                                             'if prompt.startswith("DSMv1"):'))
        runner.chmod(0o755)
        log = root / "calls.json"
        env = dict(os.environ, FAKE_RUNNER_LOG=str(log),
                   FAKE_RUNNER_PROMPT_RESPONSE='{"teacher_id":"T04","reason":"Same complete cable meaning."}')
        spec = dict(schema_version=1,
            prompt=dict(id="DSMv1", path=str(ROOT / "distillation-review-v1/matching-prompt.md")),
            dataset=dict(adapter="distillation_matching", path=str(self.path)),
            runner=dict(provider="openai-codex", auth_file=None, model="gpt-6.1-sol",
                reasoning_effort="xhigh", concurrency=8, runner_binary=str(runner),
                output_schema_path=str(ROOT / "distillation-review-v1/matching-response-schema.json")))
        (root / "spec.json").write_text(json.dumps(spec))
        def cli(*args):
            result = subprocess.run([sys.executable, str(ROOT / "experiment.py"), *map(str, args)],
                env=env, cwd=root, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            return result.stdout
        cli("prepare", "prepared", "--spec", "spec.json", "--repeat")
        report = json.loads(cli("show", "prepared", "--json"))
        self.assertEqual(report["summary"]["attempts"], 0)
        self.assertEqual(report["qualification"]["status"], "pending")
        self.assertEqual(report["qualification"]["pending"], ["M01", "M02"])
        self.assertEqual(report["prepared_inputs"]["max_teacher_subjects"], 10)
        self.assertEqual(report["requests"]["reusable"], 0)
        self.assertFalse(log.exists())
        plan = json.loads((root / "prepared/experiment.json").read_text())["plan"]
        self.assertIn("distillation_matching.py", plan["code"])
        self.assertEqual(plan["runner"]["reasoning_effort"], "xhigh")
        self.assertEqual(plan["runner"]["concurrency"], 8)
        self.assertEqual(cli("show", "prepared", "--case", "M01", "--prompt-only"),
                         report["cases"][0]["prompt"])
        # The executable is a local fixture: this exercises actual receipts,
        # decoding and native report aggregation without a provider request.
        cli("run", "prepared")
        report = json.loads(cli("show", "prepared", "--json"))
        self.assertEqual(report["summary"]["valid"], 2)
        self.assertEqual(report["qualification"]["status"], "failed")
        self.assertEqual(report["qualification"]["errors"]["false_match"], ["M02"])
        self.assertEqual(report["qualification"]["mechanical_failures"], [])

    def test_reusable_partitions_have_disjoint_notes_and_balanced_controls(self):
        source_path = ROOT / "distillation-review-v1/matching-source.json"
        notes = {}
        for partition in ("development", "confirmation"):
            spec = json.loads((ROOT / f"distillation-review-v1/matching-{partition}-spec.json").read_text())
            cases, _, _ = inputs.prepare_file(spec["dataset"], source_path,
                (ROOT / "distillation-review-v1/matching-prompt.md").read_text())
            self.assertEqual(len(cases), 16)
            self.assertEqual(sum(c["evidence"]["expected_teacher_id"] is not None for c in cases), 8)
            notes[partition] = {case["evidence"]["note_id"] for case in cases}
        self.assertFalse(notes["development"] & notes["confirmation"])

    def actual_source(self):
        root = self.path.parent
        messages = [dict(role="user", content="ASv6.100\n\n<post>\nTwo metres.\n</post>")]
        teacher = [dict(number="1", context="Cable.", subject="Cable A"),
                   dict(number="1.1", context="Length.", subject="2 m cable A")]
        references = [dict(note_id="note-a", split="evaluation", text="Two metres.", subjects=teacher)]
        evaluation = [dict(note_id="note-a", messages=messages)]
        for name, rows in (("references", references), ("evaluation", evaluation)):
            (root / (name + ".jsonl")).write_text("\n".join(json.dumps(r) for r in rows) + "\n")
        manifest = dict(schema_version=2, tasks=dict(subjects="ASv6.100"),
            train_note_ids=["train-a"], evaluation_note_ids=["note-a"], test_note_ids=["test-a"],
            subject_instruction_sha256=hashlib.sha256(b"ASv6.100").hexdigest(),
            outputs={name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                     for name in ("references.jsonl", "evaluation.jsonl")})
        (root / "manifest.json").write_text(json.dumps(manifest))
        generation = dict(note_id="note-a", messages=messages,
            answer=dict(raw=json.dumps(dict(subjects=[teacher[0],
                dict(number="1.1", context="Length.", subject="Cable A, two metres long")])),
                tokens=50, truncated=False))
        saved = root / "baseline/note-0000/subjects.json"
        saved.parent.mkdir(parents=True)
        saved.write_text(json.dumps(generation))
        def bound(path):
            return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        self.source = dict(schema_version=2, dataset_manifest=bound(root / "manifest.json"),
            cases=[dict(id="R01", generation={**bound(saved), "index": 0, "note_id": "note-a"},
                student_number="1.1", expected_teacher_number="1.1",
                expected_reason="Same cable and length, assessed before reviewer calls.",
                expectation_status="agent_assessed", selection="Saved validation wording.")])
        self.write()
        return saved, generation

    def test_actual_validation_wording_is_bound_and_not_rewritten(self):
        saved, _ = self.actual_source()
        cases, protected, preparation = self.prepare()
        case = cases[0]
        payload = json.loads(case["inputs"]["MATCH_INPUT"])
        self.assertEqual(payload["student_subject"], "Cable A, two metres long")
        self.assertEqual(payload["teacher_subjects"], [dict(id="T01", subject="Cable A"),
                                                      dict(id="T02", subject="2 m cable A")])
        self.assertEqual(case["evidence"]["expected_teacher_id"], "T02")
        self.assertEqual(case["evidence"]["expectation_status"], "agent_assessed")
        self.assertEqual(preparation["qualification_case_ids"], ["R01"])
        self.assertIn(str(saved.resolve()), protected)
        self.assertEqual(len(protected), 5)
        self.assertFalse(any(Path(p).name in {"train.jsonl", "test.jsonl"} for p in protected))
        for forbidden in ("expected", "note-a", "selection", "baseline", "agent_assessed", "<post>"):
            self.assertNotIn(forbidden, case["prompt"])
        # Agreement with an unverified expectation cannot qualify the reviewer.
        result = self.validate(case, dict(teacher_id="T02", reason="Same cable and length."))
        report = matching.qualification([{**case, **result}], ["R01"])
        self.assertEqual(report["status"], "pending")
        self.assertEqual(report["unverified_expectations"], ["R01"])

    def test_actual_source_rejects_changed_inputs_and_incomplete_answers(self):
        saved, generation = self.actual_source()
        original = copy.deepcopy(self.source)
        for mutation, expected in (("hash", "hash differs"), ("messages", "input differs"),
                                   ("note", "identity differs"), ("truncated", "output limit")):
            with self.subTest(mutation=mutation):
                self.source = copy.deepcopy(original)
                value = copy.deepcopy(generation)
                if mutation == "messages":
                    value["messages"][0]["content"] += "CHANGED"
                elif mutation == "note":
                    value["note_id"] = "test-a"
                elif mutation == "truncated":
                    value["answer"]["truncated"] = True
                saved.write_text(json.dumps(value))
                if mutation != "hash":
                    self.source["cases"][0]["generation"]["sha256"] = hashlib.sha256(saved.read_bytes()).hexdigest()
                else:
                    self.source["cases"][0]["generation"]["sha256"] = "0" * 64
                self.write()
                with self.assertRaisesRegex(ValueError, expected):
                    self.prepare()

    def test_final_test_path_is_rejected_before_opening_it(self):
        self.actual_source()
        self.source["cases"][0]["generation"]["path"] = str(self.path.parent / "test/note-0000/subjects.json")
        self.write()
        with self.assertRaisesRegex(ValueError, "validation generation"):
            self.prepare()

    def test_nonobject_source_is_rejected_as_a_source_error(self):
        self.source = []
        self.write()
        with self.assertRaisesRegex(ValueError, "matching source fields"):
            self.prepare()

    def test_unresolved_expectation_does_not_become_a_negative_gold_label(self):
        self.actual_source()
        self.source["cases"][0].update(expectation_status="unresolved", expected_teacher_number=None,
            expected_reason="The complete wording needs adjudication before assigning an expected match.")
        self.write()
        case = self.prepare()[0][0]
        result = self.validate(case, dict(teacher_id="T02", reason="Same cable and length."))
        self.assertIsNone(result["qualification"]["passed"])
        self.assertIsNone(result["qualification"]["error"])
        report = matching.qualification([{**case, **result}], ["R01"])
        self.assertEqual(report["status"], "pending")
        self.assertEqual(report["checked"], 0)
        self.assertEqual(report["unresolved_expectations"], ["R01"])


if __name__ == "__main__":
    unittest.main()
