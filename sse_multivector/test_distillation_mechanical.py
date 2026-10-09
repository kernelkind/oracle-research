"""Native mechanical routing for source-bound distillation checks, without providers."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from sse_multivector.test_extraction_pipeline import FAKE_RUNNER


ROOT = Path(__file__).resolve().parent
PROMPTS = ROOT / "distillation-review-v1"


class DistillationMechanicalTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.log = self.root / "calls.json"
        worker = self.root / "fake-runner"
        worker.write_text(FAKE_RUNNER.replace('if prompt.startswith("GENERIC PROMPT"):',
            'if prompt.startswith(("DSMv1", "DSSv1", "DSLv1")):'))
        worker.chmod(0o755)
        self.worker = worker
        self.environment = dict(os.environ, FAKE_RUNNER_LOG=str(self.log))

    def write(self, name, value):
        path = self.root / name
        path.write_text(json.dumps(value))
        return path

    def cli(self, *args, response=None):
        environment = dict(self.environment)
        if response is not None:
            environment["FAKE_RUNNER_PROMPT_RESPONSE"] = json.dumps(response)
        result = subprocess.run([sys.executable, str(ROOT / "experiment.py"), *map(str, args)],
            cwd=self.root, env=environment, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout

    def show(self, experiment):
        return json.loads(self.cli("show", experiment, "--json"))

    def spec(self, check, *, mixed=False, contradictory=False):
        reference = PROMPTS / "teacher-relative-source.json"
        bound = dict(path=str(reference), sha256=hashlib.sha256(reference.read_bytes()).hexdigest())
        if check == "matching":
            cases = [dict(id="copied", case="TC01", student_number="1.2.1.1", replacements=[],
                expected_teacher_number=None if contradictory else "1.2.1.1",
                expected_reason="Explicit fixture expectation.", partition="development")]
            if mixed:
                cases.append(dict(id="semantic", case="TC02", student_number="1.1.1.1", replacements=[],
                    expected_teacher_number="1.1.1.1", expected_reason="Same cable and length.",
                    partition="development"))
            source = dict(schema_version=1, review_source=bound, cases=cases)
            adapter, prompt_id, prompt, schema = ("distillation_matching", "DSMv1", "matching-prompt.md",
                                                "matching-response-schema.json")
        else:
            cases = [dict(id="copied", case="TC01", student_number="1.2.1.1",
                          expected_reason="The unchanged trusted teacher subject and edge.")]
            if mixed:
                cases.append(dict(id="semantic", case="TC02" if check == "support" else "TC04",
                    student_number="1.1.1.1" if check == "support" else "1.1.1.2",
                    expected_reason="Existing authored control."))
            source = dict(schema_version=1, check=check, review_source=bound, cases=cases)
            adapter = "distillation_verdict"
            prompt_id = "DSSv1" if check == "support" else "DSLv1"
            prompt, schema = check + "-prompt-v1.md", "boolean-response-schema.json"
        source_path = self.write(check + "-source.json", source)
        return self.write(check + "-spec.json", dict(schema_version=1,
            prompt=dict(id=prompt_id, path=str(PROMPTS / prompt)),
            dataset=dict(adapter=adapter, path=str(source_path)),
            runner=dict(provider="openai-codex", auth_file=None, model="gpt-6.1-sol",
                reasoning_effort="xhigh", concurrency=2, runner_binary=str(self.worker),
                output_schema_path=str(PROMPTS / schema))))

    def assert_witness(self, check, case):
        self.assertEqual(case["origin"], "mechanical")
        self.assertEqual(case["attempts"], 0)
        self.assertFalse(case["reused"])
        self.assertNotIn("receipt", case)
        self.assertEqual(case["output"], case["mechanical"]["output"])
        self.assertEqual(case["parsed"], json.loads(case["output"]))
        if check == "relationship":
            expected = dict(rule="exact_teacher_relationship", teacher_relationships=[
                dict(parent="1.1.1.1.1", child="1.1.1.1.1.1"),
                dict(parent="1.1.2.1.1", child="1.1.2.1.1.1"),
                dict(parent="1.2.1", child="1.2.1.1")])
        else:
            expected = dict(rule="exact_teacher_subject", teacher_numbers=[
                "1.1.1.1.1.1", "1.1.2.1.1.1", "1.1.3.1", "1.2.1.1"])
        self.assertEqual(case["mechanical_evidence"], expected)
        self.assertEqual(case["mechanical"]["evidence"], expected)
        self.assertNotIn(expected["rule"], case["prompt"])
        if check == "matching":
            self.assertEqual(case["parsed"]["teacher_id"], "T10")
        else:
            self.assertIs(case["parsed"]["valid"], True)

    def test_all_three_checks_prepare_and_run_without_worker_or_attempt_budget_usage(self):
        for check in ("matching", "support", "relationship"):
            with self.subTest(check=check):
                budget = self.write(check + "-budget.json", dict(schema_version=1, limit=1, used=1))
                original_budget = budget.read_bytes()
                self.cli("prepare", check, "--spec", self.spec(check))
                prepared = self.show(check)
                self.assert_witness(check, prepared["cases"][0])
                self.assertEqual(prepared["summary"]["mechanical"], 1)
                self.assertEqual(prepared["summary"]["attempts"], 0)
                self.assertEqual(prepared["requests"]["new"], 0)
                self.assertEqual(prepared["qualification"]["mechanical_cases"], ["copied"])
                self.assertEqual(prepared["qualification"]["model_checked"], 0)
                if check == "matching":
                    self.assertEqual(prepared["prepared_inputs"]["calls"], 0)
                    self.assertEqual(prepared["prepared_inputs"]["rendered_input_tokens"], 0)
                self.cli("run", check, "--attempt-budget", budget, "--max-new-attempts", "1")
                after = self.show(check)
                self.assert_witness(check, after["cases"][0])
                self.assertEqual(after["summary"]["attempts"], 0)
                self.assertEqual(after["usage"]["input_tokens"], 0)
                self.assertEqual(budget.read_bytes(), original_budget)
                self.assertFalse(self.log.exists())
                self.assertFalse((self.root / check / "run/results.jsonl").exists())

    def test_mixed_checks_dispatch_and_charge_only_the_semantic_case(self):
        for check in ("matching", "support", "relationship"):
            with self.subTest(check=check):
                experiment = check + "-mixed"
                budget = self.write(check + "-budget.json", dict(schema_version=1, limit=1, used=0))
                self.cli("prepare", experiment, "--spec", self.spec(check, mixed=True))
                before = self.show(experiment)
                self.assertEqual(before["requests"]["new"], 1)
                self.assertEqual(before["summary"]["attempts"], 0)
                self.assertEqual(before["summary"]["mechanical"], 1)
                semantic = next(case for case in before["cases"] if case["id"] == "semantic")
                self.assertEqual(semantic["status"], "unrun")
                if check == "matching":
                    self.assertEqual(before["prepared_inputs"]["calls"], 1)
                    response = dict(teacher_id="T04", reason="Same complete cable and length.")
                else:
                    response = dict(valid=check == "support", reason="Fixture semantic verdict.")
                self.cli("run", experiment, "--attempt-budget", budget, "--max-new-attempts", "1",
                         response=response)
                after = self.show(experiment)
                cases = {case["id"]: case for case in after["cases"]}
                self.assert_witness(check, cases["copied"])
                self.assertIn("receipt", cases["semantic"])
                self.assertNotEqual(cases["semantic"].get("origin"), "mechanical")
                self.assertEqual(after["summary"]["valid"], 2)
                self.assertEqual(after["summary"]["attempts"], 1)
                self.assertEqual(after["qualification"]["checked"], 2)
                self.assertEqual(after["qualification"]["model_checked"], 1)
                self.assertEqual(after["qualification"]["mechanical_cases"], ["copied"])
                self.assertEqual(json.loads(budget.read_text())["used"], 1)
                calls = json.loads(self.log.read_text())
                self.assertEqual([call["prompt"] for call in calls], [semantic["prompt"]])
                receipts = [json.loads(line) for line in
                    (self.root / experiment / "run/results.jsonl").read_text().splitlines()]
                self.assertEqual([receipt["job_key"] for receipt in receipts], ["prompt:semantic"])
                self.log.unlink()

    def test_repeat_forces_fake_model_receipts_for_all_three_mechanical_checks(self):
        for check in ("matching", "support", "relationship"):
            with self.subTest(check=check):
                original, repeated = check + "-original", check + "-repeat"
                self.cli("prepare", original, "--spec", self.spec(check))
                envelope = self.root / original / "experiment.json"
                original_bytes = envelope.read_bytes()
                self.cli("prepare", repeated, "--from", original, "--repeat")
                before = self.show(repeated)
                self.assertEqual(before["summary"]["mechanical"], 0)
                self.assertEqual(before["summary"]["unrun"], 1)
                self.assertEqual(before["requests"]["new"], 1)
                budget = self.write(check + "-budget.json", dict(schema_version=1, limit=1, used=0))
                response = (dict(teacher_id="T10", reason="Exact complete comparison.") if check == "matching"
                            else dict(valid=True, reason="Exact trusted subject or relationship."))
                self.cli("run", repeated, "--attempt-budget", budget, response=response)
                after = self.show(repeated)
                case = after["cases"][0]
                self.assertIn("receipt", case)
                self.assertNotEqual(case.get("origin"), "mechanical")
                self.assertEqual(after["summary"]["mechanical"], 0)
                self.assertEqual(after["summary"]["attempts"], 1)
                self.assertEqual(json.loads(budget.read_text())["used"], 1)
                self.assertEqual(len(json.loads(self.log.read_text())), 1)
                self.assertEqual(envelope.read_bytes(), original_bytes)
                self.assert_witness(check, self.show(original)["cases"][0])
                self.assertFalse((self.root / original / "run/results.jsonl").exists())
                self.log.unlink()

    def test_conflicting_expectation_stays_visible_and_does_not_change_mechanical_match(self):
        self.cli("prepare", "conflict", "--spec", self.spec("matching", contradictory=True))
        report = self.show("conflict")
        self.assert_witness("matching", report["cases"][0])
        self.assertIsNone(report["cases"][0]["evidence"]["expected_teacher_id"])
        self.assertFalse(report["cases"][0]["qualification"]["passed"])
        self.assertEqual(report["qualification"]["errors"]["false_match"], ["copied"])
        self.assertEqual(report["qualification"]["status"], "failed")
        self.assertEqual(report["qualification"]["model_checked"], 0)
        self.assertFalse(self.log.exists())


if __name__ == "__main__":
    unittest.main()
