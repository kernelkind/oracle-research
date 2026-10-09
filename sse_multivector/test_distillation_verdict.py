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

    def actual_source(self, check="support"):
        root = self.path.parent
        task = (ROOT / "subject-prompt-goal-v1/asv6.100/ASv6.100.md").read_text()
        post = "Cable A is 2 m long."
        messages = [dict(role="user", content=task + "\n\n<post>\n" + post + "\n</post>")]
        teacher = [dict(number="1", context="Cables.", subject="Cables"),
                   dict(number="1.1", context="Cable A.", subject="2 m cable A")]
        for name, rows in (("references", [dict(note_id="note-a", split="evaluation",
                                                text=post, subjects=teacher)]),
                           ("evaluation", [dict(note_id="note-a", messages=messages)])):
            (root / (name + ".jsonl")).write_text("\n".join(json.dumps(r) for r in rows) + "\n")
        def bound(path):
            return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        manifest = dict(schema_version=2, tasks=dict(subjects="ASv6.100"),
            train_note_ids=["train-a"], evaluation_note_ids=["note-a"], test_note_ids=["test-a"],
            subject_instruction_sha256=hashlib.sha256(task.encode()).hexdigest(),
            outputs={name: bound(root / name)["sha256"] for name in ("references.jsonl", "evaluation.jsonl")})
        (root / "manifest.json").write_text(json.dumps(manifest))
        student = [dict(number="1", context="Wrong parent.", subject="3 m cables"),
                   dict(number="1.1", context="Length.", subject="Cable A, two metres long")]
        generation = dict(note_id="note-a", messages=messages,
            answer=dict(raw=json.dumps(dict(subjects=student)), tokens=50, truncated=False))
        saved = root / "baseline/note-0000/subjects.json"
        saved.parent.mkdir(parents=True, exist_ok=True)
        saved.write_text(json.dumps(generation))
        self.source = dict(schema_version=2, check=check, dataset_manifest=bound(root / "manifest.json"),
            cases=[dict(id="A01", generation={**bound(saved), "index": 0, "note_id": "note-a"},
                student_number="1.1", expected_valid=check == "support", expectation_status="agent_assessed",
                expected_reason="Supported two-metre cable; the actual parent requires three metres.",
                selection="Untouched saved validation output.")])
        return saved, generation

    def test_actual_support_is_bound_and_does_not_promote_agent_expectations_to_gold(self):
        saved, _ = self.actual_source()
        cases, protected, _ = self.prepare()
        case = cases[0]
        self.assertEqual(json.loads(case["inputs"]["SUPPORT_INPUT"]),
                         dict(post="Cable A is 2 m long.", student_subject="Cable A, two metres long"))
        self.assertIn(str(saved.resolve()), protected)
        self.assertFalse(any(Path(p).name in {"train.jsonl", "test.jsonl"} for p in protected))
        for forbidden in ("expected_valid", "expected_reason", "agent_assessed", "baseline", "note-a"):
            self.assertNotIn(forbidden, case["prompt"])
        result = inputs.validate(dict(adapter="distillation_verdict"), case,
            '{"valid":true,"reason":"The post states the length."}', None)
        from sse_multivector import distillation_verdict as verdict
        report = verdict.qualification([{**case, **result}], ["A01"])
        self.assertTrue(result["qualification"]["passed"])
        self.assertEqual(report["status"], "pending")
        self.assertEqual(report["unverified_expectations"], ["A01"])

    def test_actual_support_accepts_authored_subject_and_preserves_source_evidence(self):
        saved, generation = self.actual_source()
        definition = self.source["cases"][0]
        definition.update(student_subject="  Cable A, four mètres long  ", expected_valid=False,
            expected_reason="The authored length differs from the original post.",
            selection="Authored support contrast bound to the saved validation subject.")
        cases, protected, preparation = self.prepare()
        case = cases[0]
        self.assertEqual(json.loads(case["inputs"]["SUPPORT_INPUT"]),
            dict(post="Cable A is 2 m long.", student_subject=definition["student_subject"]))
        task = generation["messages"][0]["content"].split("\n\n<post>\n")[0]
        end = "Derive broader headings by generalizing source meanings without adding restrictions."
        self.assertEqual(case["inputs"]["ASV6_100_SUPPORT_RULES"], task[:task.index(end) + len(end)])
        self.assertEqual(case["evidence"]["original_student_subject"], "Cable A, two metres long")
        self.assertEqual(case["evidence"]["student_subject"], definition["student_subject"])
        self.assertEqual(case["evidence"]["student_number"], "1.1")
        self.assertEqual(case["evidence"]["generation"], definition["generation"])
        self.assertEqual(case["evidence"]["expected_reason"], definition["expected_reason"])
        self.assertEqual(case["evidence"]["selection"], definition["selection"])
        self.assertEqual(json.loads(saved.read_text()), generation)
        self.assertEqual(protected[str(saved.resolve())], definition["generation"]["sha256"])
        self.assertEqual(preparation["qualification_case_ids"], ["A01"])
        for forbidden in ("Cable A, two metres long", "expected_valid", definition["expected_reason"],
                          "agent_assessed", definition["selection"], "baseline", "note-a"):
            self.assertNotIn(forbidden, case["prompt"])
        from sse_multivector import distillation_verdict as verdict
        for actual, passed in ((False, True), (True, False)):
            result = inputs.validate(dict(adapter="distillation_verdict"), case,
                json.dumps(dict(valid=actual, reason="The post gives two metres.")), None)
            self.assertEqual(result["qualification"]["passed"], passed)
            self.assertEqual(verdict.qualification([{**case, **result}], ["A01"])["status"], "pending")
        definition.update(expected_valid=None, expectation_status="unresolved")
        case = self.prepare()[0][0]
        result = inputs.validate(dict(adapter="distillation_verdict"), case,
            '{"valid":false,"reason":"The post gives two metres."}', None)
        self.assertIsNone(result["qualification"]["passed"])
        self.assertEqual(verdict.qualification([{**case, **result}], ["A01"])["unresolved_expectations"], ["A01"])

    def test_authored_support_subject_requires_nonblank_string_and_support_source_v2(self):
        authored_source = copy.deepcopy(self.source)
        for subject in (None, "", " \n\t", 1, True, [], {}):
            with self.subTest(subject=subject):
                self.actual_source()
                self.source["cases"][0]["student_subject"] = subject
                with self.assertRaisesRegex(ValueError, "student subject"):
                    self.prepare()
        self.actual_source()
        self.source["cases"][0]["student_subject_override"] = "Cable A, four metres long"
        with self.assertRaisesRegex(ValueError, "saved verdict case fields"):
            self.prepare()
        self.actual_source("relationship")
        self.source["cases"][0]["student_subject"] = "Cable A, four metres long"
        with self.assertRaisesRegex(ValueError, "saved verdict case fields"):
            self.prepare()
        self.source = authored_source
        self.source["cases"][0]["student_subject"] = "Cable A, four metres long"
        with self.assertRaisesRegex(ValueError, "verdict control fields"):
            self.prepare()

    def test_authored_support_subject_keeps_generation_number_and_prompt_bindings(self):
        saved, generation = self.actual_source()
        self.source["cases"][0]["student_subject"] = "Cable A, four metres long"
        original = copy.deepcopy(self.source)
        for mutation, expected in (("hash", "source hash differs"), ("index", "validation generation"),
                                  ("note", "validation generation"), ("number", "unknown verdict student number"),
                                  ("identity", "identity differs"), ("test", "validation generation"),
                                  ("messages", "input differs"), ("truncated", "output limit"),
                                  ("post", "prompt differs"), ("instruction", "prompt differs")):
            with self.subTest(mutation=mutation):
                self.source = copy.deepcopy(original)
                definition = self.source["cases"][0]
                value = copy.deepcopy(generation)
                if mutation == "hash":
                    definition["generation"]["sha256"] = "0" * 64
                elif mutation == "index":
                    definition["generation"]["index"] = 1
                elif mutation == "note":
                    definition["generation"]["note_id"] = "other"
                elif mutation == "number":
                    definition["student_number"] = "99"
                elif mutation == "identity":
                    value["note_id"] = "other"
                elif mutation == "test":
                    definition["generation"]["path"] = str(self.path.parent / "test/note-0000/subjects.json")
                elif mutation == "messages":
                    value["messages"][0]["content"] += "Changed"
                elif mutation == "truncated":
                    value["answer"]["truncated"] = True
                else:
                    if mutation == "post":
                        value["messages"][0]["content"] = value["messages"][0]["content"].replace("2 m long.", "4 m long.")
                    else:
                        value["messages"][0]["content"] = "Changed instructions\n" + value["messages"][0]["content"]
                    evaluation = self.path.parent / "evaluation.jsonl"
                    evaluation.write_text(json.dumps(dict(note_id="note-a", messages=value["messages"])) + "\n")
                    manifest_path = self.path.parent / "manifest.json"
                    manifest = json.loads(manifest_path.read_text())
                    manifest["outputs"]["evaluation.jsonl"] = hashlib.sha256(evaluation.read_bytes()).hexdigest()
                    manifest_path.write_text(json.dumps(manifest))
                    self.source["dataset_manifest"]["sha256"] = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
                saved.write_text(json.dumps(value))
                if mutation != "hash":
                    definition["generation"]["sha256"] = hashlib.sha256(saved.read_bytes()).hexdigest()
                with self.assertRaisesRegex(ValueError, expected):
                    self.prepare()
                self.actual_source()

    def test_actual_relationship_uses_student_parent_and_unresolved_has_no_gold_label(self):
        self.actual_source("relationship")
        case = self.prepare()[0][0]
        self.assertEqual(json.loads(case["inputs"]["RELATIONSHIP_INPUT"]),
                         dict(parent_subject="3 m cables", child_subject="Cable A, two metres long"))
        self.assertEqual(case["evidence"]["parent_number"], "1")
        self.assertNotIn("Cable A is 2 m long.", case["prompt"])
        self.source["cases"][0].update(expected_valid=None, expectation_status="unresolved")
        case = self.prepare()[0][0]
        result = inputs.validate(dict(adapter="distillation_verdict"), case,
            '{"valid":false,"reason":"A two-metre cable need not be three metres."}', None)
        from sse_multivector import distillation_verdict as verdict
        report = verdict.qualification([{**case, **result}], ["A01"])
        self.assertIsNone(result["qualification"]["passed"])
        self.assertEqual(report["checked"], 0)
        self.assertEqual(report["unresolved_expectations"], ["A01"])

    def test_actual_validation_rejects_reserved_paths_and_changed_or_truncated_answers(self):
        saved, generation = self.actual_source()
        original = copy.deepcopy(self.source)
        for mutation, expected in (("test", "validation generation"), ("messages", "input differs"),
                                   ("truncated", "output limit")):
            with self.subTest(mutation=mutation):
                self.source = copy.deepcopy(original)
                value = copy.deepcopy(generation)
                if mutation == "test":
                    self.source["cases"][0]["generation"]["path"] = str(self.path.parent / "test/note-0000/subjects.json")
                elif mutation == "messages":
                    value["messages"][0]["content"] += "Changed"
                else:
                    value["answer"]["truncated"] = True
                saved.write_text(json.dumps(value))
                self.source["cases"][0]["generation"]["sha256"] = hashlib.sha256(saved.read_bytes()).hexdigest()
                with self.assertRaisesRegex(ValueError, expected):
                    self.prepare()

    def test_cli_handles_actual_outputs_and_keeps_assessment_status(self):
        root = self.path.parent
        runner = root / "fake-runner"
        runner.write_text(FAKE_RUNNER.replace('if prompt.startswith("GENERIC PROMPT"):',
                                             'if prompt.startswith(("DSSv1", "DSLv1")):'))
        runner.chmod(0o755)
        env = dict(os.environ, FAKE_RUNNER_LOG=str(root / "calls.json"),
                   FAKE_RUNNER_PROMPT_RESPONSE='{"valid":true,"reason":"Fixture verdict."}')
        for check, prompt_id in (("support", "DSSv1"), ("relationship", "DSLv1")):
            self.actual_source(check)
            if check == "support":
                self.source["cases"][0].update(student_subject="Cable A, four metres long",
                    expected_valid=False, expected_reason="The post gives two metres, not four.",
                    selection="Authored contrast bound to the saved validation subject.")
            self.prepare()
            spec = dict(schema_version=1,
                prompt=dict(id=prompt_id, path=str(PROMPTS / (check + "-prompt-v1.md"))),
                dataset=dict(adapter="distillation_verdict", path=str(self.path)),
                runner=dict(provider="openai-codex", auth_file=None, model="gpt-6.1-sol",
                    reasoning_effort="xhigh", concurrency=8, runner_binary=str(runner)))
            (root / "spec.json").write_text(json.dumps(spec))
            def cli(*args):
                result = subprocess.run([sys.executable, str(ROOT / "experiment.py"), *map(str, args)],
                    env=env, cwd=root, capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                return result.stdout
            cli("prepare", check, "--spec", "spec.json")
            before = json.loads(cli("show", check, "--json"))
            self.assertEqual(before["summary"]["attempts"], 0)
            self.assertFalse((root / "calls.json").exists())
            if check == "support":
                case = before["cases"][0]
                self.assertEqual(json.loads(case["inputs"]["SUPPORT_INPUT"])["student_subject"],
                                 "Cable A, four metres long")
                self.assertEqual(case["evidence"]["original_student_subject"], "Cable A, two metres long")
                self.assertEqual(case["evidence"]["student_subject"], "Cable A, four metres long")
            cli("run", check)
            after = json.loads(cli("show", check, "--json"))
            self.assertEqual(after["summary"]["valid"], 1)
            self.assertEqual(after["qualification"]["status"], "pending")
            self.assertEqual(after["qualification"]["unverified_expectations"], ["A01"])
            self.assertEqual(after["qualification"]["incorrect_verdicts"], ["A01"])
            (root / "calls.json").unlink()

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
