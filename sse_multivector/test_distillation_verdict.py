"""Single support/link judgments through production preparation and reporting."""
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
from sse_multivector.test_extraction_pipeline import FAKE_RUNNER


ROOT = Path(__file__).resolve().parent
PROMPTS = ROOT / "distillation-review-v1"


class DistillationVerdictTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / "source.json"
        reference = PROMPTS / "teacher-relative-source.json"
        self.source = dict(schema_version=1, check="support",
            review_source=dict(path=str(reference),
                sha256=hashlib.sha256(reference.read_bytes()).hexdigest()),
            cases=[dict(id="S01", case="TC02", student_number="1.1.1.1",
                        expected_reason="The post states cable A's two-metre length."),
                   dict(id="S02", case="TC03", student_number="1.2.1.1",
                        expected_reason="The comparison's negation has been reversed.")])

    def prepare(self, select=None):
        self.path.write_text(json.dumps(self.source))
        name = "support" if self.source["check"] == "support" else "relationship"
        dataset = dict(adapter="distillation_verdict")
        if select is not None:
            dataset["select"] = select
        return inputs.prepare_file(dataset, self.path,
                                   (PROMPTS / (name + "-prompt-v1.md")).read_text())

    def test_support_loads_verbatim_rules_one_subject_and_separate_expectations(self):
        cases, protected, preparation = self.prepare()
        case = cases[0]
        self.assertEqual(set(case["inputs"]), {"ASV6_100_SUPPORT_RULES", "SUPPORT_INPUT"})
        payload = json.loads(case["inputs"]["SUPPORT_INPUT"])
        self.assertEqual(set(payload), {"post", "student_subject"})
        self.assertEqual(payload["student_subject"], "Cable A, two metres long")
        self.assertEqual(payload["post"],
            "2 cables: cable A is 2 m long and cable B is 3 m long. A is not longer than B.")
        task = (ROOT / "subject-prompt-goal-v1/asv6.100/ASv6.100.md").read_text()
        end = "Derive broader headings by generalizing source meanings without adding restrictions."
        self.assertEqual(case["inputs"]["ASV6_100_SUPPORT_RULES"], task[:task.index(end) + len(end)])
        self.assertEqual([c["evidence"]["expected_valid"] for c in cases], [True, False])
        self.assertIn(str(self.path.resolve()), protected)
        self.assertEqual(len(protected), 3)
        self.assertEqual(preparation["qualification_case_ids"], ["S01", "S02"])
        for forbidden in ("expected_valid", "expected_reason", "TC02", "1.1.1.1", "teacher_subjects"):
            self.assertNotIn(forbidden, case["prompt"])

    def links(self):
        self.source["check"] = "relationship"
        self.source["cases"] = [
            dict(id="L01", case="TC02", student_number="1.1.1.1", expected_reason="Length retained."),
            dict(id="L02", case="TC03", student_number="1.2.1.1", expected_reason="Both cables retained."),
            dict(id="L03", case="TC04", student_number="1.1.1.2", expected_reason="Three metres is not two.")]

    def test_relationship_derives_actual_immediate_parent_and_excludes_post(self):
        self.links()
        cases, _, _ = self.prepare()
        self.assertEqual(set(cases[0]["inputs"]), {"ASV6_100_PARENT_CHILD_RULES", "RELATIONSHIP_INPUT"})
        self.assertEqual(json.loads(cases[0]["inputs"]["RELATIONSHIP_INPUT"]),
            dict(parent_subject="2 m cables", child_subject="Cable A, two metres long"))
        self.assertEqual(json.loads(cases[2]["inputs"]["RELATIONSHIP_INPUT"]),
            dict(parent_subject="2 m cables", child_subject="3 m cables"))
        self.assertEqual([c["evidence"]["expected_valid"] for c in cases], [True, True, False])
        task = (ROOT / "subject-prompt-goal-v1/asv6.100/ASv6.100.md").read_text()
        start = "Judge each parent-child pair using only its `subject` strings across possible posts in any domain."
        end = "The post's domain, `context` and other entries cannot supply a missing heading restriction."
        self.assertEqual(cases[0]["inputs"]["ASV6_100_PARENT_CHILD_RULES"],
                         task[task.index(start):task.index(end) + len(end)])
        for case in cases:
            self.assertNotIn("2 cables: cable A", case["prompt"])
            self.assertNotIn("expected_valid", case["prompt"])

    def test_binding_selection_and_bad_case_definitions_are_rejected(self):
        self.assertEqual([c["id"] for c in self.prepare(["S02"])[0]], ["S02"])
        for selection in (["unknown"], ["S01", "S01"], []):
            with self.subTest(selection=selection), self.assertRaises((ValueError, inputs.engine.RunnerError)):
                self.prepare(selection)
        original = copy.deepcopy(self.source)
        for mutation in ("hash", "check", "case", "number", "duplicate", "reason"):
            self.source = copy.deepcopy(original)
            if mutation == "hash":
                self.source["review_source"]["sha256"] = "0" * 64
            elif mutation == "check":
                self.source["check"] = "unknown"
            elif mutation == "case":
                self.source["cases"][0]["case"] = "unknown"
            elif mutation == "number":
                self.source["cases"][0]["student_number"] = "99"
            elif mutation == "duplicate":
                self.source["cases"][1]["id"] = "S01"
            else:
                self.source["cases"][0]["expected_reason"] = " "
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                self.prepare()
        self.source = original
        self.links()
        self.source["cases"][0]["student_number"] = "1"
        with self.assertRaisesRegex(ValueError, "immediate parent"):
            self.prepare()

    def test_boolean_contract_and_semantic_errors_remain_separate(self):
        cases, _, _ = self.prepare()
        dataset = dict(adapter="distillation_verdict")
        for case, verdict in ((cases[0], True), (cases[1], False)):
            result = inputs.validate(dataset, case, json.dumps(dict(valid=verdict, reason="Decisive wording.")), None)
            self.assertTrue(result["qualification"]["passed"])
            result = inputs.validate(dataset, case, json.dumps(dict(valid=not verdict, reason="Wrong judgment.")), None)
            self.assertEqual(result["status"], "valid")
            self.assertFalse(result["qualification"]["passed"])
        for value in (dict(valid=1, reason="Numeric."), dict(valid="true", reason="String."),
                      dict(valid=True, reason=" "), dict(valid=True), dict(valid=True, reason="OK", extra=True)):
            with self.subTest(value=value), self.assertRaises(ValueError):
                inputs.validate(dataset, cases[0], json.dumps(value), None)
        with self.assertRaises(ValueError):
            inputs.validate(dataset, cases[0], '{"valid":true,"valid":false,"reason":"Duplicate."}', None)

    def test_cli_prepares_without_calls_and_reports_fixture_verdicts(self):
        self.prepare()
        root = self.path.parent
        runner = root / "fake-runner"
        runner.write_text(FAKE_RUNNER.replace('if prompt.startswith("GENERIC PROMPT"):',
                                             'if prompt.startswith("DSSv1"):'))
        runner.chmod(0o755)
        log = root / "calls.json"
        env = dict(os.environ, FAKE_RUNNER_LOG=str(log),
                   FAKE_RUNNER_PROMPT_RESPONSE='{"valid":true,"reason":"The post supports it."}')
        spec = dict(schema_version=1,
            prompt=dict(id="DSSv1", path=str(PROMPTS / "support-prompt-v1.md")),
            dataset=dict(adapter="distillation_verdict", path=str(self.path)),
            runner=dict(provider="openai-codex", auth_file=None, model="gpt-6.1-sol",
                reasoning_effort="xhigh", concurrency=8, runner_binary=str(runner)))
        (root / "spec.json").write_text(json.dumps(spec))
        def cli(*args):
            result = subprocess.run([sys.executable, str(ROOT / "experiment.py"), *map(str, args)],
                env=env, cwd=root, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            return result.stdout
        cli("prepare", "prepared", "--spec", "spec.json")
        report = json.loads(cli("show", "prepared", "--json"))
        self.assertEqual(report["summary"]["attempts"], 0)
        self.assertEqual(report["qualification"]["status"], "pending")
        self.assertEqual(report["qualification"]["pending"], ["S01", "S02"])
        self.assertFalse(log.exists())
        plan = json.loads((root / "prepared/experiment.json").read_text())["plan"]
        self.assertIn("distillation_verdict.py", plan["code"])
        self.assertIn("distillation_review.py", plan["code"])
        self.assertEqual(plan["runner"]["concurrency"], 8)
        self.assertEqual(plan["runner"]["reasoning_effort"], "xhigh")
        self.assertEqual(cli("show", "prepared", "--case", "S01", "--prompt-only"), report["cases"][0]["prompt"])
        # Only the local executable fixture is called, never a model/provider.
        cli("run", "prepared")
        report = json.loads(cli("show", "prepared", "--json"))
        self.assertEqual(report["summary"]["valid"], 2)
        self.assertEqual(report["qualification"]["status"], "failed")
        self.assertEqual(report["qualification"]["incorrect_verdicts"], ["S02"])
        self.assertEqual(report["qualification"]["mechanical_failures"], [])
