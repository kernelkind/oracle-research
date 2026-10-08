"""Offline checks through the shared experiment preparation and validation paths."""
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

from sse_multivector import experiment_inputs as inputs
from sse_multivector.distillation_run import parse_subjects
from sse_multivector.test_extraction_pipeline import FAKE_RUNNER


ROOT = Path(__file__).resolve().parent
AS = ROOT / "subject-prompt-goal-v1/asv6.100/ASv6.100.md"


def cumin_case():
    example = re.findall(r"<example>(.*?)</example>", AS.read_text(), re.S)[7]
    teacher = parse_subjects(re.search(r"<output>(.*?)</output>", example, re.S)[1])
    student = [entry for entry in teacher if entry["number"] != "3.1"]
    groups = {}
    for entry in teacher:
        groups.setdefault(entry["subject"], []).append(entry["number"])
    report = dict(schema_version=1, prompt_id="DSRv1",
                  subjects=[dict(number=e["number"], valid=True, reason="Supported by the post.")
                            for e in student],
                  relationships=[dict(parent=e["number"].rpartition(".")[0], child=e["number"],
                                      valid=True, reason="The child preserves the parent restrictions.")
                                 for e in student if "." in e["number"]], coverage=[])
    for subject, numbers in groups.items():
        required = "1.1" in numbers or "1.1.1" in numbers
        compatible = []
        if "1.1" in numbers:
            compatible = ["1", "1.1", "2", "2.1"]
        elif "1.1.1" in numbers:
            compatible = [e["number"] for e in student]
        report["coverage"].append(dict(teacher_numbers=numbers, required=required,
            student_numbers=[e["number"] for e in student if e["subject"] == subject],
            compatible_heading_numbers=compatible, reason="Required complete source or optional broader heading."))
    payload = dict(post=re.search(r"<post>\s*(.*?)\s*</post>", example, re.S)[1],
                   teacher=teacher, student=student, teacher_meanings=None,
                   exact_matches=[dict(teacher_number=t["number"], student_number=s["number"])
                                  for t in teacher for s in student if t["subject"] == s["subject"]])
    return dict(id="Q17", inputs=dict(TASK_PROMPT=AS.read_text(),
                                      REVIEW_INPUT=json.dumps(payload))), report


class DistillationReviewTests(unittest.TestCase):
    def validate(self, case, report):
        return inputs.validate(dict(adapter="distillation_review"), case, json.dumps(report), None)

    def test_missing_branch_scores_coverage_separately_from_correctness(self):
        case, report = cumin_case()
        result = inputs.validate(dict(adapter="distillation_review"), case, json.dumps(report), None)
        self.assertIn("scores", result)
        self.assertEqual(result["scores"]["correctness"], dict(numerator=9, denominator=9, value=1.0))
        self.assertEqual(result["scores"]["coverage"], dict(numerator=1, denominator=2, value=0.5))
        missing = [row for row in result["findings"]["coverage"] if not row["covered"]]
        self.assertEqual(len(missing), 1)
        self.assertEqual(missing[0]["missing_heading_numbers"], ["3"])

    def test_incomplete_invented_and_contradictory_reports_remain_ungraded(self):
        case, report = cumin_case()
        changes = []
        bad = copy.deepcopy(report); bad["subjects"].pop(); changes.append(bad)
        bad = copy.deepcopy(report); bad["relationships"].pop(); changes.append(bad)
        bad = copy.deepcopy(report); bad["relationships"][0]["parent"] = "4"; changes.append(bad)
        bad = copy.deepcopy(report); bad["subjects"].append(bad["subjects"][0]); changes.append(bad)
        bad = copy.deepcopy(report); bad["subjects"][0]["reason"] = " "; changes.append(bad)
        bad = copy.deepcopy(report); bad["subjects"][0]["valid"] = "true"; changes.append(bad)
        bad = copy.deepcopy(report); bad["coverage"].pop(); changes.append(bad)
        bad = copy.deepcopy(report); bad["coverage"][0]["student_numbers"] = []; changes.append(bad)
        bad = copy.deepcopy(report); bad["coverage"][0]["student_numbers"] = ["99"]; changes.append(bad)
        bad = copy.deepcopy(report); bad["coverage"][0]["compatible_heading_numbers"] = ["1"]; changes.append(bad)
        for bad in changes:
            with self.subTest(report=bad), self.assertRaises(ValueError):
                self.validate(case, bad)
        for raw in ('{"schema_version":1,"schema_version":1}', json.dumps(report)[:-1]):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                inputs.validate(dict(adapter="distillation_review"), case, raw, None)

    def test_a_bad_subject_and_incoming_link_count_as_one_bad_entry(self):
        case, report = cumin_case()
        next(row for row in report["subjects"] if row["number"] == "1.1.1")["valid"] = False
        next(row for row in report["relationships"] if row["child"] == "1.1.1")["valid"] = False
        result = self.validate(case, report)
        self.assertEqual(result["scores"]["correctness"], dict(numerator=8, denominator=9, value=8 / 9))
        self.assertEqual(len(result["findings"]["incorrect_subjects"]), 1)
        self.assertEqual(len(result["findings"]["invalid_relationships"]), 1)

    def test_number_prefix_is_not_ancestry_and_an_equal_heading_covers_itself(self):
        entry = lambda number, subject: dict(number=number, subject=subject, context="Cable A is 2 m long.")
        teacher = [entry("1", "2 m cable A")]
        student = [entry("1", "Cables"), entry("1.1", "2 m cables"), entry("1.10", "2 m cable A")]
        payload = dict(post="Cable A is 2 m long.", teacher=teacher, student=student,
                       exact_matches=[dict(teacher_number="1", student_number="1.10")], teacher_meanings=None)
        case = dict(inputs=dict(REVIEW_INPUT=json.dumps(payload)))
        report = dict(schema_version=1, prompt_id="DSRv1",
            subjects=[dict(number=e["number"], valid=True, reason="Supported.") for e in student],
            relationships=[dict(parent="1", child=number, valid=True, reason="Preserves restrictions.")
                           for number in ("1.1", "1.10")],
            coverage=[dict(teacher_numbers=["1"], required=True, student_numbers=["1.10"],
                           compatible_heading_numbers=["1", "1.1", "1.10"], reason="Complete source.")])
        result = self.validate(case, report)
        self.assertEqual(result["findings"]["coverage"][0]["missing_heading_numbers"], ["1.1"])
        report["coverage"][0]["compatible_heading_numbers"].remove("1.1")
        self.assertEqual(self.validate(case, report)["scores"]["coverage"]["value"], 1)

    def test_frozen_teacher_groups_cannot_change_between_versions(self):
        case, report = cumin_case()
        payload = json.loads(case["inputs"]["REVIEW_INPUT"])
        payload["teacher_meanings"] = [{key: row[key] for key in ("teacher_numbers", "required")}
                                       for row in report["coverage"]]
        case["inputs"]["REVIEW_INPUT"] = json.dumps(payload)
        self.validate(case, report)
        row = next(row for row in report["coverage"] if row["required"])
        row.update(required=False, compatible_heading_numbers=[])
        with self.assertRaisesRegex(ValueError, "fixed reference"):
            self.validate(case, report)

    def test_output_failures_score_zero_while_reviewer_failures_are_ungraded(self):
        from sse_multivector import distillation_review as review
        case, report = cumin_case()
        raw = json.dumps(dict(subjects=json.loads(case["inputs"]["REVIEW_INPUT"])["student"]))
        for output, truncated in ((raw[:-1], False), (raw, True),
                ('{"subjects":[{"number":"1.0","context":"x","subject":"x"}]}', False)):
            with self.subTest(output=output, truncated=truncated):
                result = review.score_saved_output(case, output, truncated=truncated)
                self.assertEqual(result["status"], "output_failure")
                self.assertEqual([score["value"] for score in result["scores"].values()], [0, 0])
        for reviewer in (None, "{", json.dumps({**report, "subjects": []})):
            with self.subTest(reviewer=reviewer), self.assertRaises(ValueError):
                review.score_saved_output(case, raw, reviewer)
        with self.assertRaisesRegex(ValueError, "frozen review input"):
            review.score_saved_output(case, '{"subjects":[]}', json.dumps(report))

    def test_saved_outputs_use_the_existing_subject_parser_contract(self):
        from sse_multivector import distillation_review as review
        case, report = cumin_case()
        raw = json.dumps(dict(subjects=json.loads(case["inputs"]["REVIEW_INPUT"])["student"]))
        result = review.score_saved_output(case, "```json\n" + raw + "\n```", json.dumps(report))
        self.assertEqual(result["status"], "valid")
        duplicate = '{"subjects": [], "subjects": []}'
        self.assertEqual(review.score_saved_output(case, duplicate)["status"], "output_failure")
        with self.assertRaisesRegex(ValueError, "missing"):
            review.score_saved_output(case, None)

    def test_empty_output_conventions_and_wrong_verdicts_are_visible(self):
        case, report = cumin_case()
        payload = json.loads(case["inputs"]["REVIEW_INPUT"])
        payload.update(student=[], exact_matches=[])
        case["inputs"]["REVIEW_INPUT"] = json.dumps(payload)
        report.update(subjects=[], relationships=[])
        for row in report["coverage"]:
            row.update(student_numbers=[], compatible_heading_numbers=[])
        self.assertEqual([score["value"] for score in self.validate(case, report)["scores"].values()], [0, 0])
        payload.update(teacher=[], teacher_meanings=[])
        case["inputs"]["REVIEW_INPUT"] = json.dumps(payload)
        report["coverage"] = []
        self.assertEqual([score["value"] for score in self.validate(case, report)["scores"].values()], [1, 1])
        case, report = cumin_case()
        case["evidence"] = dict(expected=dict(scores=dict(correctness=[1, 1], coverage=[1, 1])))
        result = self.validate(case, report)
        self.assertEqual(result["status"], "valid")
        self.assertFalse(result["qualification"]["passed"])
        self.assertIn("coverage", result["qualification"]["differences"][0])

    def test_qualification_catalog_prepares_all_worked_example_variants(self):
        cases, _, _ = inputs.prepare_file(dict(adapter="distillation_review",
            select=[f"Q{i:02}" for i in range(1, 20)]), ROOT / "distillation-review-v1/qualification-source.json",
            (ROOT / "distillation-review-v1/prompt.md").read_text())
        self.assertEqual(len(cases), 19)
        by_id = {case["id"]: json.loads(case["inputs"]["REVIEW_INPUT"]) for case in cases}
        self.assertIsNone(by_id["Q06"]["teacher_meanings"])
        self.assertIsNone(by_id["Q08"]["teacher_meanings"])
        self.assertEqual([len(by_id[key]["student"]) for key in ("Q12", "Q13", "Q16", "Q18", "Q19")],
                         [14, 15, 12, 0, 1])
        moved = next(entry for entry in by_id["Q13"]["student"] if entry["number"] == "1.1.1.2")
        self.assertEqual(moved["subject"], "3 m cables")
        q17 = next(case for case in cases if case["id"] == "Q17")
        _, report = cumin_case()
        self.assertTrue(self.validate(q17, report)["qualification"]["passed"])

    def test_initial_teacher_classification_is_checked_without_giving_away_labels(self):
        cases, _, _ = inputs.prepare_file(dict(adapter="distillation_review", select=["Q08"]),
            ROOT / "distillation-review-v1/qualification-source.json",
            (ROOT / "distillation-review-v1/prompt.md").read_text())
        case = cases[0]
        payload = json.loads(case["inputs"]["REVIEW_INPUT"])
        self.assertIsNone(payload["teacher_meanings"])
        report = json.loads((ROOT / "distillation-review-v1/tests/fixtures/Q17-report.json").read_text())
        report["subjects"].append(dict(number="3.1", valid=True, reason="Complete supported cumin source."))
        report["relationships"].append(dict(parent="3", child="3.1", valid=True, reason="Explicitly names cumin."))
        cumin = next(row for row in report["coverage"] if "3.1" in row["teacher_numbers"])
        cumin["student_numbers"].append("3.1")
        cumin["compatible_heading_numbers"].append("3.1")
        self.assertTrue(self.validate(case, report)["qualification"]["passed"])
        for row in report["coverage"]:
            row.update(required=False, compatible_heading_numbers=[])
        # Both aggregate scores still equal one. The wrong classifications must fail.
        result = self.validate(case, report)
        self.assertEqual(result["scores"]["coverage"]["value"], 1)
        self.assertFalse(result["qualification"]["passed"])
        self.assertTrue(any("known control" in reason for reason in result["qualification"]["differences"]))

    def test_qualification_requires_all_cases_and_preserves_relative_judgments(self):
        from sse_multivector import distillation_review as review
        case, report = cumin_case()
        case.update(id="baseline", evidence=dict(expected={}))
        baseline = dict(case, **self.validate(case, report))
        changed = copy.deepcopy(baseline)
        changed.update(id="changed")
        changed["evidence"] = dict(expected=dict(relative_to="baseline"),
                                  definition=dict(changes=[dict(op="replace", numbers=["1.1.1"],
                                                               old="to taste", new="according to taste")]))
        self.assertEqual(review.qualification([baseline], ["baseline", "changed"])["status"], "pending")
        self.assertEqual(review.qualification([baseline, changed], ["baseline", "changed"])["status"], "passed")
        changed["parsed"]["subjects"][0]["valid"] = False
        result = review.qualification([baseline, changed], ["baseline", "changed"])
        self.assertEqual(result["status"], "failed")
        self.assertIn("beyond", result["differences"][0])

    def test_preparation_uses_bound_sources_and_keeps_expectations_outside_the_prompt(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "source.json"
            path.write_text(json.dumps(dict(schema_version=1,
                task_prompt=dict(path=str(AS), sha256=hashlib.sha256(AS.read_bytes()).hexdigest()),
                references={"C8": dict(format="as_example", index=8,
                    required_meanings=[["1.1", "2.1"], ["1.1.1", "2.1.1", "3.1", "4.1"]])},
                cases=[dict(id="Q17", reference="C8", changes=[dict(op="remove", numbers=["3.1"])],
                    expected=dict(scores=dict(correctness=[9, 9], coverage=[1, 2])))])))
            cases, sources, _ = inputs.prepare_file(dict(adapter="distillation_review"), path,
                                                     "{TASK_PROMPT}\n{REVIEW_INPUT}")
            case = cases[0]
            payload = json.loads(case["inputs"]["REVIEW_INPUT"])
            self.assertEqual(len(payload["teacher"]), 10)
            self.assertEqual(len(payload["student"]), 9)
            self.assertNotIn("expected", payload)
            self.assertIn("expected", case["evidence"])
            self.assertEqual(sources[str(AS)], hashlib.sha256(AS.read_bytes()).hexdigest())
            self.assertEqual(case["inputs"]["TASK_PROMPT"], AS.read_text())
            definition = json.loads(path.read_text())
            definition["task_prompt"]["sha256"] = "0" * 64
            path.write_text(json.dumps(definition))
            with self.assertRaisesRegex(ValueError, "source hash"):
                inputs.prepare_file(dict(adapter="distillation_review"), path, "{TASK_PROMPT}\n{REVIEW_INPUT}")

    def test_cli_prepares_and_scores_a_supplied_fixture_without_inference(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runner = root / "runner"
            runner.write_text(FAKE_RUNNER)
            runner.chmod(0o755)
            log = root / "calls.json"
            env = dict(os.environ, FAKE_RUNNER_LOG=str(log))
            source = dict(schema_version=1,
                task_prompt=dict(path=str(AS), sha256=hashlib.sha256(AS.read_bytes()).hexdigest()),
                references={"C8": dict(format="as_example", index=8,
                    required_meanings=[["1.1", "2.1"], ["1.1.1", "2.1.1", "3.1", "4.1"]])},
                cases=[dict(id="Q17", reference="C8", changes=[dict(op="remove", numbers=["3.1"])],
                    expected=dict(scores=dict(correctness=[9, 9], coverage=[1, 2])))])
            (root / "source.json").write_text(json.dumps(source))
            spec = dict(schema_version=1, prompt=dict(id="DSRv1", path=str(ROOT / "distillation-review-v1/prompt.md")),
                dataset=dict(adapter="distillation_review", path="source.json"),
                runner=dict(runner_binary=str(runner), provider="openai-codex", model="gpt-6.1-sol",
                    reasoning_effort="xhigh", concurrency=1, auth_file=None,
                    output_schema_path=str(ROOT / "distillation-review-v1/response-schema.json")))
            (root / "spec.json").write_text(json.dumps(spec))
            def cli(*args):
                result = subprocess.run([sys.executable, str(ROOT / "experiment.py"), *map(str, args)],
                    cwd=root, env=env, capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                return result.stdout
            cli("prepare", "prepared", "--spec", "spec.json")
            shown = json.loads(cli("show", "prepared", "--case", "Q17"))
            self.assertEqual(shown["status"], "unrun")
            rendered = cli("show", "prepared", "--case", "Q17", "--prompt-only")
            self.assertEqual(rendered, shown["prompt"])
            self.assertNotIn('"expected"', shown["prompt"])
            plan = json.loads((root / "prepared/experiment.json").read_text())["plan"]
            self.assertIn("distillation_review.py", plan["code"])
            _, fixture = cumin_case()
            (root / "fixture.json").write_text(json.dumps(fixture))
            scored = json.loads(cli("score-review", "prepared", "--case", "Q17", "--report", "fixture.json"))
            self.assertEqual(scored["source_kind"], "supplied_report")
            self.assertEqual(scored["scores"]["coverage"]["value"], 0.5)
            self.assertTrue(scored["qualification"]["passed"])
            self.assertFalse(log.exists())


if __name__ == "__main__":
    unittest.main()
