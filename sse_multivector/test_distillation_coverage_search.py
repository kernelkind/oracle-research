"""Focused coverage search through native production preparation and validation."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from sse_multivector import experiment_inputs


class DistillationCoverageSearchTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def test_native_cli_exposes_coverage_search_preparation(self):
        project = Path(__file__).resolve().parents[1]
        launcher = project.parent / "experiment-runner/bin/experiment-runner"
        result = subprocess.run([sys.executable, str(launcher), "--project-root", str(project),
            "prepare-distillation-coverage-search", "--help"], cwd=project,
            capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("--answer-id", result.stdout)

    def test_null_requires_every_candidate_and_positive_requires_only_the_witness(self):
        case = dict(inputs=dict(COVERAGE_INPUT=json.dumps(dict(teacher_subject="Cable A", candidates=[
            dict(student_number="1", student_subject="Fruits", teacher_contexts=[]),
            dict(student_number="1.1", student_subject="Cables", teacher_contexts=[])]))),
            evidence=dict(expected_compatible_heading_numbers=None))
        dataset = dict(adapter="distillation_coverage_search")
        negative = dict(evidence=[dict(student_number="1", reason="Fruit restriction is absent.")],
                        witness_student_number=None)
        with self.assertRaisesRegex(ValueError, "every candidate"):
            experiment_inputs.validate(dataset, case, json.dumps(negative), None)
        negative["evidence"].append(dict(student_number="1.1", reason="Cable restriction is absent."))
        result = experiment_inputs.validate(dataset, case, json.dumps(negative), None)
        self.assertEqual(result["status"], "valid")
        positive = dict(evidence=[dict(student_number="1.1", reason="Cable A is a cable.")],
                        witness_student_number="1.1")
        self.assertEqual(experiment_inputs.validate(dataset, case, json.dumps(positive), None)["parsed"], positive)
        for bad in (dict(positive, witness_student_number="99"),
                    dict(positive, evidence=negative["evidence"]),
                    dict(positive, evidence=[dict(student_number="1.1", reason=" ")])):
            with self.assertRaises(ValueError):
                experiment_inputs.validate(dataset, case, json.dumps(bad), None)

    def baseline(self, name, *, edge_valid=None, student=None, teacher=None):
        from sse_multivector import test_distillation_review_evaluation as fixtures
        from sse_multivector import distillation_review_evaluation as evaluation
        from sse_multivector import distillation_review_assessment as assessment
        fixture = fixtures.DistillationReviewEvaluationTests()
        fixture.root = self.root
        teacher = teacher or fixtures.subjects(("1", "Fruits"), ("2", "Cable A"))
        student = fixtures.subjects(("1", "Fruits"), ("1.1", "Cables"), ("2", "Cable A")) if student is None else student
        selected = fixture.selection([dict(note_id="validation-" + name, post="Cable A. Fruit.",
            teacher=teacher, answer=fixtures.answer(student))], name=name)
        context = self.root / (name + "-assessment")
        assessment.record(selected, "R01", context,
            teacher_meanings=[dict(teacher_numbers=[row["number"]], required=row["subject"] == "Cable A")
                              for row in teacher], reason="Independent complete fixture meanings.")
        worker = fixture.worker()
        if edge_valid is False:
            worker.write_text(worker.read_text().replace('else {"valid": True, "reason": "Fixture semantic verdict."}',
                'else {"valid": not prompt.startswith("DSLv2"), "reason": "Fixture semantic verdict."}'))
        output = self.root / (name + "-baseline")
        prepared = evaluation.prepare(selected, output, runner_binary=worker, assessment_directory=context)
        for entry in prepared["experiments"]:
            if edge_valid is not None or entry["check"] != "relationship":
                fixture.native("run", entry["path"], "--max-new-attempts", 10)
        return fixture, output, worker

    def test_native_preparation_retains_invalid_or_unknown_children_and_only_shrinks_valid_edges(self):
        from sse_multivector import distillation_coverage_search as coverage
        for index, edge_valid in enumerate((False, None, True)):
            with self.subTest(edge_valid=edge_valid):
                fixture, baseline, worker = self.baseline(str(index), edge_valid=edge_valid)
                output = self.root / (str(index) + "-coverage")
                prepared = coverage.prepare(baseline, output, runner_binary=worker)
                self.assertEqual(prepared["search_cases"], 1)
                self.assertEqual(prepared["inference_calls"], 0)
                guard = prepared["preparation"]["matching_self_guards"]
                self.assertEqual([(row["student_number"], row["valid"]) for row in guard], [("2", True)])
                native = json.loads(fixture.native("show", prepared["experiments"][0]["path"], "--json"))
                case = native["cases"][0]
                expected = ["1"] if edge_valid is True else ["1", "1.1"]
                self.assertEqual(case["evidence"]["candidate_student_numbers"], expected)
                payload = json.loads(case["inputs"]["COVERAGE_INPUT"])
                self.assertEqual([row["student_number"] for row in payload["candidates"]], expected)
                self.assertNotIn("expected_compatible", case["prompt"])
                self.assertEqual(native["settings"]["model"], "gpt-6.1-sol")
                self.assertEqual(native["settings"]["reasoning_effort"], "xhigh")
                self.assertEqual(native["settings"]["concurrency"], 30)
                plan = json.loads((Path(prepared["experiments"][0]["path"]) / "experiment.json").read_text())["plan"]
                self.assertIn(str(baseline / "evaluation.json"), plan["sources"])
                if edge_valid is True:
                    omitted = case["evidence"]["omitted_descendants"]
                    self.assertEqual(omitted[0]["student_number"], "1.1")
                    self.assertIn("Conditional", omitted[0]["semantic_status"])

    def test_native_frozen_search_rejects_changed_premise_snapshot(self):
        from sse_multivector import distillation_coverage_search as coverage
        fixture, baseline, worker = self.baseline("changed", edge_valid=True)
        prepared = coverage.prepare(baseline, self.root / "changed-coverage", runner_binary=worker)
        snapshot = baseline / "evaluation.json"
        snapshot.write_bytes(snapshot.read_bytes() + b"\n")
        plan = json.loads((Path(prepared["experiments"][0]["path"]) / "experiment.json").read_text())["plan"]
        with self.assertRaisesRegex(ValueError, "evaluation hash differs"):
            experiment_inputs.prepare_file(plan["dataset"], Path(plan["dataset"]["path"]), plan["prompt"]["text"])

    def test_identical_uncovered_subjects_and_contexts_share_a_candidate_with_explicit_aliases(self):
        from sse_multivector import distillation_coverage_search as coverage
        from sse_multivector import test_distillation_review_evaluation as fixtures
        fixture, baseline, worker = self.baseline("duplicates", edge_valid=False,
            student=fixtures.subjects(("1", "Fruits"), ("2", "Fruits"), ("3", "Cable A")))
        prepared = coverage.prepare(baseline, self.root / "duplicate-coverage", runner_binary=worker)
        native = json.loads(fixture.native("show", prepared["experiments"][0]["path"], "--json"))
        case = native["cases"][0]
        self.assertEqual(case["evidence"]["candidate_student_numbers"], ["1"])
        self.assertEqual(case["evidence"]["candidate_aliases"], [
            dict(representative_student_number="1", student_numbers=["1", "2"])])
        self.assertEqual(case["evidence"]["original_uncovered_heading_numbers"], ["1", "2"])

    def test_omitted_baseline_positive_exposes_end_to_end_disagreement_without_becoming_gold(self):
        case = dict(inputs=dict(COVERAGE_INPUT=json.dumps(dict(teacher_subject="Cable A", candidates=[
            dict(student_number="1", student_subject="Fruits", teacher_contexts=[])]))),
            evidence=dict(original_uncovered_heading_numbers=["1", "1.1"], baseline_compatibility=[
                dict(student_number="1", status="valid", valid=False),
                dict(student_number="1.1", status="valid", valid=True)]))
        negative = dict(evidence=[dict(student_number="1", reason="Fruit restriction is absent.")],
                        witness_student_number=None)
        result = experiment_inputs.validate(dict(adapter="distillation_coverage_search"), case,
            json.dumps(negative), None)
        self.assertIsNone(result["qualification"]["passed"])
        self.assertTrue(result["qualification"]["candidate_baseline_agreement"])
        self.assertFalse(result["qualification"]["coverage_baseline_agreement"])
        case["evidence"]["baseline_compatibility"][1]["valid"] = None
        result = experiment_inputs.validate(dict(adapter="distillation_coverage_search"), case,
            json.dumps(negative), None)
        self.assertIsNone(result["qualification"]["coverage_baseline_agreement"])

    def test_no_match_covered_and_trusted_missing_placement_are_settled_without_search(self):
        from sse_multivector import distillation_coverage_search as coverage
        from sse_multivector import test_distillation_review_evaluation as fixtures
        variants = [
            ("missing", fixtures.subjects(("1", "Fruits")), None, "no_full_match"),
            ("covered", fixtures.subjects(("1", "Cable A")), None, "no_uncovered_heading"),
            ("trusted", fixtures.subjects(("1", "Cables"), ("2", "Cable A")),
             fixtures.subjects(("1", "Cables"), ("1.1", "Cable A")), "trusted_uncovered_compatible_heading")]
        for name, student, teacher, rule in variants:
            with self.subTest(rule=rule):
                _, baseline, worker = self.baseline(name, student=student, teacher=teacher, edge_valid=True)
                prepared = coverage.prepare(baseline, self.root / (name + "-coverage"), runner_binary=worker)
                self.assertEqual(prepared["search_cases"], 0)
                self.assertEqual(prepared["experiments"], [])
                self.assertEqual(prepared["preparation"]["settlements"][0]["rule"], rule)


if __name__ == "__main__":
    unittest.main()
