"""Focused coverage search through native production preparation and validation."""
import hashlib
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
        self.assertIn("--premise-audit", result.stdout)

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

    def baseline(self, name, *, edge_valid=None, student=None, teacher=None, matching_teacher_id=None,
                 required_subjects=("Cable A",)):
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
        meanings = {}
        for row in teacher:
            meanings.setdefault(row["subject"], dict(teacher_numbers=[], required=row["subject"] in required_subjects))[
                "teacher_numbers"].append(row["number"])
        assessment.record(selected, "R01", context,
            teacher_meanings=list(meanings.values()), reason="Independent complete fixture meanings.")
        worker = fixture.worker()
        if matching_teacher_id is not None:
            worker.write_text(worker.read_text().replace('{"teacher_id": None,',
                '{"teacher_id": ' + json.dumps(matching_teacher_id) + ','))
        if edge_valid is False:
            worker.write_text(worker.read_text().replace('else {"valid": True, "reason": "Fixture semantic verdict."}',
                'else {"valid": not prompt.startswith("DSLv2"), "reason": "Fixture semantic verdict."}'))
        output = self.root / (name + "-baseline")
        prepared = evaluation.prepare(selected, output, runner_binary=worker, assessment_directory=context)
        for entry in prepared["experiments"]:
            if edge_valid is not None or entry["check"] != "relationship":
                fixture.native("run", entry["path"], "--max-new-attempts", 10)
        return fixture, output, worker

    def path_baseline(self, name, *, teacher=None, matching_teacher_id="T01", edge_valid=True,
                      required_subjects=("Cable A",)):
        from sse_multivector import distillation_review_evaluation as evaluation
        from sse_multivector import test_distillation_review_evaluation as fixtures
        fixture, baseline, worker = self.baseline(name, edge_valid=edge_valid,
            teacher=teacher or fixtures.subjects(("1", "Cables"), ("1.1", "Cable A")),
            student=fixtures.subjects(("1", "Cables in general"), ("2", "Cable A")),
            matching_teacher_id=matching_teacher_id, required_subjects=required_subjects)
        original = evaluation.report(baseline)
        parent = original["random"]["answers"][0]["checks"]["matching"][0]
        native = next(row for row in original["experiments"]
                      if any(case["id"] == parent["id"] for case in row["cases"])
                      and row["cases"][0]["evidence"]["check"] == "matching")
        return fixture, baseline, worker, parent, native

    def test_accepted_complete_match_reuses_a_trusted_teacher_path_with_provenance(self):
        from sse_multivector import distillation_coverage_search as coverage
        fixture, baseline, worker, parent, native = self.path_baseline("matched-path")
        fixture.native("review", native["experiment"], "--case", parent["id"],
            "--role", "agent", "--verdict", "accept", "--comment", "Complete matching output audited.")
        prepared = coverage.prepare(baseline, self.root / "matched-path-coverage", runner_binary=worker)
        self.assertEqual(prepared["search_cases"], 0)
        self.assertEqual(prepared["inference_calls"], 0)
        settlement = prepared["preparation"]["settlements"][0]
        self.assertEqual(settlement["rule"], "accepted_matching_trusted_teacher_path")
        self.assertFalse(settlement["covered"])
        self.assertEqual(settlement["witness_student_number"], "1")
        premise = settlement["matching_premise"]
        self.assertEqual(premise["case_id"], parent["id"])
        self.assertEqual(premise["input_sha256"], parent["input_sha256"])
        self.assertEqual(premise["output_sha256"], hashlib.sha256(parent["output"].encode()).hexdigest())
        self.assertEqual([row["number"] for row in settlement["teacher_path"]], ["1", "1.1"])
        self.assertTrue(all("context" in row for row in settlement["teacher_path"]))
        self.assertIn("Conditional", settlement["semantic_status"])
        self.assertIn(str(Path(native["experiment"]) / "reviews.jsonl"), prepared["sources"])

    def test_unaudited_disputed_and_null_matches_keep_the_search(self):
        from sse_multivector import distillation_coverage_search as coverage
        for verdict, identifier in ((None, "T01"), ("reject", "T01"), ("uncertain", "T01"), ("accept", None)):
            with self.subTest(verdict=verdict, identifier=identifier):
                name = str(verdict) + str(identifier)
                fixture, baseline, worker, parent, native = self.path_baseline(name, matching_teacher_id=identifier)
                if verdict is not None:
                    fixture.native("review", native["experiment"], "--case", parent["id"],
                        "--role", "agent", "--verdict", verdict, "--comment", "Fixture complete-output assessment.")
                prepared = coverage.prepare(baseline, self.root / (name + "-coverage"), runner_binary=worker)
                self.assertEqual(prepared["search_cases"], 1)
                self.assertFalse(prepared["preparation"]["settlements"])

    def test_only_an_actual_connected_teacher_occurrence_can_supply_the_path(self):
        from sse_multivector import distillation_coverage_search as coverage
        from sse_multivector import test_distillation_review_evaluation as fixtures
        for name, teacher, expected in (
                ("unrelated", fixtures.subjects(("1", "Cables"), ("2", "Tools"), ("2.1", "Cable A")), None),
                ("duplicate", fixtures.subjects(("1", "Cables"), ("2", "Cables"), ("2.1", "Cable A")), ["2", "2.1"])):
            with self.subTest(name=name):
                fixture, baseline, worker, parent, native = self.path_baseline(name, teacher=teacher)
                fixture.native("review", native["experiment"], "--case", parent["id"],
                    "--role", "agent", "--verdict", "accept", "--comment", "Complete matching output audited.")
                prepared = coverage.prepare(baseline, self.root / (name + "-coverage"), runner_binary=worker)
                self.assertEqual(prepared["search_cases"], 1 if expected is None else 0)
                if expected is not None:
                    self.assertEqual([row["number"] for row in prepared["preparation"]["settlements"][0]["teacher_path"]], expected)

    def test_false_and_unrun_parent_self_guards_cannot_license_reuse(self):
        from sse_multivector import distillation_coverage_search as coverage
        for state in (False, None):
            with self.subTest(state=state):
                name = "guard-" + str(state)
                fixture, baseline, worker, parent, native = self.path_baseline(name, edge_valid=state,
                    required_subjects=("Cables", "Cable A"))
                fixture.native("review", native["experiment"], "--case", parent["id"],
                    "--role", "agent", "--verdict", "accept", "--comment", "Complete matching output audited.")
                prepared = coverage.prepare(baseline, self.root / (name + "-coverage"), runner_binary=worker)
                self.assertGreater(prepared["search_cases"], 0)
                self.assertNotIn("accepted_matching_trusted_teacher_path",
                    [row["rule"] for row in prepared["preparation"]["settlements"]])

    def test_native_cli_binds_existing_exact_output_audits_and_rejects_changed_audit_bytes(self):
        from sse_multivector import distillation_coverage_search as coverage
        fixture, baseline, worker, parent, _ = self.path_baseline("audit-path")
        row = dict(check="matching", input_sha256=parent["input_sha256"],
            output_sha256=hashlib.sha256(parent["output"].encode()).hexdigest(),
            verdict="accept", reason="Complete saved matching output audited.")
        audit = self.root / "complete-output-audit.jsonl"
        audit.write_text(json.dumps(dict(record_type="skip", check="relationship")) + "\n" + json.dumps(row) + "\n")
        prepared = json.loads(fixture.native("prepare-distillation-coverage-search", baseline,
            "--output", self.root / "audit-coverage", "--premise-audit", audit, "--runner-binary", worker))
        self.assertEqual(prepared["search_cases"], 0)
        premise = prepared["preparation"]["settlements"][0]["matching_premise"]
        self.assertEqual(premise["audits"][0]["line"], 2)
        self.assertEqual(premise["audits"][0]["sha256"], prepared["sources"][str(audit)])
        source = dict(schema_version=1, evaluation=prepared["evaluation"], answer_ids=prepared["answer_ids"],
            premise_audits=[dict(path=str(audit), sha256=prepared["sources"][str(audit)])])
        audit.write_bytes(audit.read_bytes() + b"\n")
        with self.assertRaisesRegex(ValueError, "premise audit hash differs"):
            coverage.prepare_source(source, baseline)

    def test_stale_native_acceptance_and_other_output_audits_cannot_license_reuse(self):
        from sse_multivector import distillation_coverage_search as coverage
        fixture, baseline, worker, parent, _ = self.path_baseline("stale-audit")
        audit = self.root / "other-output-audit.jsonl"
        audit.write_text(json.dumps(dict(check="matching", input_sha256=parent["input_sha256"],
            output_sha256="0" * 64, verdict="accept", reason="A different output was audited.")) + "\n")
        prepared = coverage.prepare(baseline, self.root / "other-output-coverage", runner_binary=worker, premise_audits=[audit])
        self.assertEqual(prepared["search_cases"], 1)
        stale = dict(parent, reviews=[dict(verdict="accept", current=False)])
        self.assertIsNone(coverage._accepted_premise(stale, {}))

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
