"""Complete saved-answer review preparation through the native runner."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from sse_multivector import test_distillation_review_preview as preview_fixtures

answer, subjects = preview_fixtures.answer, preview_fixtures.subjects


PROJECT = Path(__file__).resolve().parents[1]
LAUNCHER = PROJECT.parent / "experiment-runner/bin/experiment-runner"


class DistillationReviewEvaluationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def fixture(self, notes=None, *, name="fixture"):
        fixture = preview_fixtures.DistillationReviewPreviewTests()
        fixture.root = self.root
        return fixture.fixture(notes, name=name)

    def selection(self, notes=None, *, name="fixture"):
        from sse_multivector.distillation_review_trial import prepare_trial
        manifest, outputs = self.fixture(notes, name=name)
        result = prepare_trial(manifest, outputs, self.root / ("selection-" + name), random_count=1, hard_count=0,
                               seed="native-evaluation-fixture")
        return Path(result["selection_path"])

    def worker(self):
        worker = self.root / "fake-runner"
        text = (PROJECT.parent / "experiment-runner/tests/fixtures/fake-runner.py").read_text()
        text = text.replace('if prompt.startswith("GENERIC PROMPT"):',
                            'if prompt.startswith(("DSMv3", "DSSv2", "DSLv2")):')
        text = text.replace('if stage == "prompt":',
            'if stage == "prompt":\n'
            '    os.environ["FAKE_RUNNER_PROMPT_RESPONSE"] = json.dumps('
            '{"teacher_id": None, "reason": "Fixture unmatched wording."} if prompt.startswith("DSMv3") '
            'else {"valid": True, "reason": "Fixture semantic verdict."})')
        worker.write_text(text)
        worker.chmod(0o755)
        return worker

    def native(self, *args):
        result = subprocess.run([sys.executable, str(LAUNCHER), "--project-root", str(PROJECT),
            *map(str, args)], cwd=PROJECT,
            env=dict(os.environ, FAKE_RUNNER_LOG=str(self.root / "calls.json")),
            capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout

    def test_prepare_preserves_complete_occurrences_and_native_mechanics_without_calls(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        selected = self.selection()
        prepared = evaluation.prepare(selected, self.root / "evaluation", runner_binary=self.worker())
        cases = {name: [] for name in ("matching", "support", "relationship")}
        for entry in prepared["experiments"]:
            report = json.loads(self.native("show", entry["path"], "--json"))
            cases[entry["check"]].extend(report["cases"])
            self.assertEqual(report["settings"]["model"], "gpt-6.1-sol")
            self.assertEqual(report["settings"]["reasoning_effort"], "xhigh")
            self.assertEqual(report["settings"]["concurrency"], 8)
            self.assertEqual(report["settings"]["timeout_seconds"], 3600)
        self.assertEqual({name: len(rows) for name, rows in cases.items()},
                         dict(matching=11, support=11, relationship=6))
        self.assertEqual(sum(case.get("origin") == "mechanical" for rows in cases.values() for case in rows), 13)
        self.assertTrue(all(case["evidence"]["expectation_status"] == "unresolved"
                            for rows in cases.values() for case in rows))
        self.assertFalse((self.root / "calls.json").exists())

    def test_preparation_summary_counts_native_distinct_requests_and_remaining_work(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        prepared = evaluation.prepare(self.selection(), self.root / "evaluation", runner_binary=self.worker())
        requests = prepared["summary"]["requests"]
        self.assertEqual({name: row["distinct"] for name, row in requests["checks"].items()},
                         dict(matching=4, support=4, relationship=2))
        self.assertEqual(requests["totals"], dict(distinct=10, remaining=10, reusable=0, new=10,
                                                warmups_remaining=0))
        with patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.root / "calls.json")):
            complete = evaluation.run(self.root / "evaluation", max_new_attempts=10)
        self.assertEqual(complete["summary"]["requests"]["totals"],
                         dict(distinct=10, remaining=0, reusable=0, new=0, warmups_remaining=0))

    def test_native_run_dispatches_identical_inputs_once_and_joins_all_occurrences(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        prepared = evaluation.prepare(self.selection(), self.root / "evaluation", runner_binary=self.worker())
        for entry in prepared["experiments"]:
            self.assertFalse(entry["prefix_cached"])
            self.native("run", entry["path"], "--max-new-attempts", 10)
        report = evaluation.report(self.root / "evaluation")
        selected = report["random"]["answers"][0]
        self.assertEqual(selected["status"], "complete")
        self.assertEqual(selected["coverage"]["status"], "pending")
        self.assertEqual({check: len(rows) for check, rows in selected["checks"].items()},
                         dict(matching=11, support=11, relationship=6))
        self.assertEqual(len(json.loads((self.root / "calls.json").read_text())), 10)
        all_cases = [case for rows in selected["checks"].values() for case in rows]
        self.assertEqual(sum(case.get("reused", False) for case in all_cases), 5)
        self.assertEqual(sum(case.get("origin") == "mechanical" for case in all_cases), 13)
        repeated = [case for case in selected["checks"]["support"]
                    if case["evidence"]["student_number"] in ("1.3", "1.4")]
        self.assertEqual([case["parsed"] for case in repeated], [repeated[0]["parsed"]] * 2)
        self.assertEqual(report["generation_usage"]["original_calls"], 10)
        self.assertEqual(report["generation_usage"]["input_tokens"], 1000)
        self.assertEqual(report["generation_usage"]["output_tokens"], 200)
        self.assertEqual(report["generation_usage"]["reasoning_tokens"], 50)

    def test_only_long_repeated_natural_prefixes_get_native_warmups(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        post, parent = 'A "quoted" note.\n' + "word " * 1100, "Broad " * 1100
        teacher = subjects(("1", parent), ("1.1", "2 m cable A"))
        student = subjects(("1", parent), ("1.1", "First new wording"),
                           ("1.2", "Second new wording"), ("1.3", "First new wording"))
        prepared = evaluation.prepare(self.selection([dict(note_id="validation-a", post=post,
            teacher=teacher, answer=answer(student))]), self.root / "evaluation", runner_binary=self.worker())
        cached = [entry for entry in prepared["experiments"] if entry["prefix_cached"]]
        self.assertEqual({entry["check"] for entry in cached}, {"matching", "support", "relationship"})
        self.assertEqual(prepared["summary"]["requests"]["totals"],
                         dict(distinct=6, remaining=6, reusable=0, new=6, warmups_remaining=3))
        budget = self.root / "budget.json"
        budget.write_text(json.dumps(dict(schema_version=1, limit=9, used=0)))
        with patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.root / "calls.json")):
            report = evaluation.run(self.root / "evaluation", max_new_attempts=9, attempt_budget_path=budget)
        self.assertEqual(report["random"]["answers"][0]["status"], "complete")
        self.assertEqual(len(json.loads((self.root / "calls.json").read_text())), 9)
        self.assertEqual(json.loads(budget.read_text())["used"], 9)
        self.assertEqual(sum(native.get("cache_warmup", {}).get("attempts", 0)
                             for native in report["experiments"]), 3)
        for native in report["experiments"]:
            if native.get("cache_warmup", {}).get("attempts", 0):
                self.assertEqual(native["summary"]["reused"], 1)
                self.assertEqual(native["generation_usage"]["original_calls"], 3)

    def test_context_compatibility_uses_native_relationship_mechanics_and_complete_coverage(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        from sse_multivector import distillation_review_assessment as assessment
        teacher = subjects(("1", "Cables"), ("1.1", "2 m cable A"))
        selected = self.selection([dict(note_id="validation-a", post="Cable A is 2 m long.",
                                        teacher=teacher, answer=answer(teacher))])
        context = self.root / "assessment"
        assessment.record(selected, "R01", context, teacher_meanings=[
            dict(teacher_numbers=["1"], required=False), dict(teacher_numbers=["1.1"], required=True)],
            reason="Frozen independent fixture teacher meanings.")
        prepared = evaluation.prepare(selected, self.root / "evaluation", runner_binary=self.worker(),
                                      assessment_directory=context)
        for entry in prepared["experiments"]:
            self.native("run", entry["path"], "--max-new-attempts", 1)
        report = evaluation.report(self.root / "evaluation")
        result = report["random"]["answers"][0]
        relationships = result["checks"]["relationship"]
        self.assertEqual(len(relationships), 3)
        self.assertEqual(sum(case["evidence"]["role"] == "actual_relationship" for case in relationships), 1)
        self.assertEqual(sum(case["evidence"]["role"] == "compatibility" for case in relationships), 2)
        self.assertTrue(all(case["origin"] == "mechanical" for rows in result["checks"].values() for case in rows))
        self.assertEqual(result["coverage"]["status"], "complete")
        self.assertEqual(result["scores"]["coverage"]["value"], 1)
        self.assertEqual(result["scores"]["correctness"]["value"], 1)
        self.assertFalse((self.root / "calls.json").exists())

    def test_shared_native_execution_cap_and_budget_cover_every_group_and_resume(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        prepared = evaluation.prepare(self.selection(), self.root / "evaluation", runner_binary=self.worker())
        budget = self.root / "budget.json"
        budget.write_text(json.dumps(dict(schema_version=1, limit=10, used=0)))
        with patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.root / "calls.json")):
            partial = evaluation.run(self.root / "evaluation", max_new_attempts=3, attempt_budget_path=budget)
            self.assertEqual(len(json.loads((self.root / "calls.json").read_text())), 3)
            self.assertEqual(json.loads(budget.read_text())["used"], 3)
            self.assertEqual(partial["random"]["answers"][0]["status"], "pending")
            complete = evaluation.run(self.root / "evaluation", max_new_attempts=20, attempt_budget_path=budget)
        self.assertEqual(complete["random"]["answers"][0]["status"], "complete")
        self.assertEqual(json.loads(budget.read_text())["used"], 10)
        self.assertEqual(len(json.loads((self.root / "calls.json").read_text())), 10)

    def test_missing_match_under_compatible_heading_fails_existing_coverage_rule(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        from sse_multivector import distillation_review_assessment as assessment
        teacher = subjects(("1", "Cables"), ("1.1", "2 m cable A"), ("2", "Tools"))
        student = subjects(("1", "Cables"), ("1.1", "Tools"), ("2", "2 m cable A"))
        selected = self.selection([dict(note_id="validation-a", post="Cable A is 2 m long. Tools.",
                                        teacher=teacher, answer=answer(student))])
        context = self.root / "assessment"
        assessment.record(selected, "R01", context, teacher_meanings=[
            dict(teacher_numbers=["1"], required=False), dict(teacher_numbers=["1.1"], required=True),
            dict(teacher_numbers=["2"], required=False)], reason="Independent fixture reference context.")
        worker = self.worker()
        worker.write_text(worker.read_text().replace('else {"valid": True, "reason": "Fixture semantic verdict."}',
                                                     'else {"valid": False, "reason": "Fixture semantic verdict."}'))
        prepared = evaluation.prepare(selected, self.root / "evaluation", runner_binary=worker, assessment_directory=context)
        for entry in prepared["experiments"]:
            self.native("run", entry["path"], "--max-new-attempts", 10)
        result = evaluation.report(self.root / "evaluation")["random"]["answers"][0]
        self.assertEqual(result["coverage"]["status"], "complete")
        self.assertEqual(result["scores"]["coverage"]["value"], 0)
        self.assertEqual(result["coverage"]["findings"][0]["matched_student_numbers"], ["2"])
        self.assertEqual(result["coverage"]["findings"][0]["missing_heading_numbers"], ["1"])
        self.assertEqual(result["scores"]["correctness"]["value"], 2 / 3)

    def test_changed_saved_sources_and_assessment_snapshot_reject_reporting(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        from sse_multivector import distillation_review_assessment as assessment
        selected = self.selection()
        context = self.root / "assessment"
        assessment.record(selected, "R01", context, teacher_meanings=[
            dict(teacher_numbers=["1"], required=False), dict(teacher_numbers=["1.1", "1.2"], required=True),
            dict(teacher_numbers=["1.3"], required=True), dict(teacher_numbers=["2"], required=False),
            dict(teacher_numbers=["2.1"], required=True)], reason="Frozen fixture source meanings.")
        evaluation.prepare(selected, self.root / "evaluation", runner_binary=self.worker(), assessment_directory=context)
        path = next(context.glob("teacher-*.json"))
        original = path.read_bytes()
        path.write_bytes(original + b"\n")
        with self.assertRaisesRegex(ValueError, "snapshot|hash"):
            evaluation.report(self.root / "evaluation")
        path.write_bytes(original)
        generation = Path(json.loads(selected.read_text())["random"]["answers"][0]["generation"]["path"])
        generation.write_bytes(generation.read_bytes() + b"\n")
        with self.assertRaisesRegex(ValueError, "hash"):
            evaluation.report(self.root / "evaluation")
        self.assertFalse((self.root / "calls.json").exists())

    def test_invalid_and_valid_empty_answers_preserve_zero_scores_without_dispatch(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        from sse_multivector import distillation_review_assessment as assessment
        teacher = subjects(("1", "Cables"), ("1.1", "2 m cable A"))
        for name, saved in (("invalid", answer([], raw="not JSON")), ("empty", answer([]))):
            with self.subTest(output=name):
                selected = self.selection([dict(note_id="validation-a", post="Cable A is 2 m long.",
                    teacher=teacher, answer=saved)], name=name)
                context = self.root / (name + "-assessment")
                assessment.record(selected, "R01", context, teacher_meanings=[
                    dict(teacher_numbers=["1"], required=False), dict(teacher_numbers=["1.1"], required=True)],
                    reason="Independent required source meaning.")
                output = self.root / (name + "-evaluation")
                prepared = evaluation.prepare(selected, output, runner_binary=self.worker(), assessment_directory=context)
                self.assertEqual(prepared["experiments"], [])
                result = evaluation.report(output)["random"]["answers"][0]
                self.assertEqual(result["status"], "invalid_output" if name == "invalid" else "complete")
                for metric in ("correctness", "coverage"):
                    self.assertEqual(result["scores"][metric]["value"], 0)
        self.assertFalse((self.root / "calls.json").exists())

    def test_frozen_expected_scores_and_case_qualifications_are_separate_from_prompts(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        from sse_multivector import distillation_review_assessment as assessment
        teacher = subjects(("1", "Cables"), ("1.1", "2 m cable A"))
        selected = self.selection([dict(note_id="validation-a", post="Cable A is 2 m long.",
                                        teacher=teacher, answer=answer(teacher))])
        context = self.root / "assessment"
        assessment.record(selected, "R01", context, teacher_meanings=[
            dict(teacher_numbers=["1"], required=False), dict(teacher_numbers=["1.1"], required=True)],
            reason="Independent fixture source meaning.")
        reason = "Frozen label outside every model input."
        assessment.record(selected, "R01", context, expectations=dict(
            matching=[dict(student_number=number, teacher_number=number, reason=reason) for number in ("1", "1.1")],
            support=[dict(student_number=number, valid=True, reason=reason) for number in ("1", "1.1")],
            relationships=[dict(child="1.1", valid=True, reason=reason)],
            compatibility=[dict(teacher_numbers=["1.1"], compatible_heading_numbers=["1", "1.1"], reason=reason)]),
            reason="Pre-call candidate judgments.")
        assessment.freeze(selected, context)
        prepared = evaluation.prepare(selected, self.root / "evaluation", runner_binary=self.worker(), assessment_directory=context)
        result = evaluation.report(self.root / "evaluation")
        row = result["random"]["answers"][0]
        self.assertEqual(row["expected_scores"], row["scores"])
        self.assertEqual(row["qualification"]["incorrect_cases"], [])
        self.assertEqual(row["qualification"]["score_differences"], {})
        self.assertEqual(row["qualification"]["unresolved"], [])
        self.assertEqual(result["summary"]["random"]["checks"]["relationship"]["mechanical"], 3)
        for entry in prepared["experiments"]:
            native = json.loads(self.native("show", entry["path"], "--json"))
            for case in native["cases"]:
                self.assertNotIn(reason, case["prompt"])
                self.assertIs(case["qualification"]["passed"], True)
        self.assertFalse((self.root / "calls.json").exists())

    def test_native_execution_errors_are_preserved_instead_of_allowance_exhaustion(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        from sse_multivector.extraction_pipeline import RunnerError
        evaluation.prepare(self.selection(), self.root / "evaluation", runner_binary=self.worker())
        with patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.root / "calls.json"), FAKE_RUNNER_FAIL_STAGE="prompt"):
            with self.assertRaises(RunnerError):
                evaluation.run(self.root / "evaluation", max_new_attempts=10)
        report = evaluation.report(self.root / "evaluation")
        self.assertEqual(report["random"]["answers"][0]["status"], "failed")
        self.assertEqual(len(json.loads((self.root / "calls.json").read_text())), 6)
        records = [json.loads(line) for native in report["experiments"]
                   for path in (Path(native["experiment"]) / "run/results.jsonl",)
                   if path.exists() for line in path.read_text().splitlines()]
        self.assertEqual(len(records), 6)
        self.assertTrue(all(record["attempt"] == 1 and "retry_reason" not in record for record in records))

    def test_no_match_and_unsupported_child_skip_questions_without_inventing_verdicts(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        from sse_multivector import distillation_review_assessment as assessment
        teacher = subjects(("1", "Cables"), ("1.1", "Cable A"))
        student = subjects(("1", "Unrelated root"), ("1.1", "Unrelated child"))
        selected = self.selection([dict(note_id="validation-a", post="Cable A.",
            teacher=teacher, answer=answer(student))])
        context = self.root / "assessment"
        assessment.record(selected, "R01", context, teacher_meanings=[
            dict(teacher_numbers=["1"], required=False), dict(teacher_numbers=["1.1"], required=True)],
            reason="Independent complete source meaning.")
        worker = self.worker()
        worker.write_text(worker.read_text().replace('else {"valid": True, "reason": "Fixture semantic verdict."}',
            'else {"valid": False, "reason": "Fixture semantic verdict."}'))
        evaluation.prepare(selected, self.root / "evaluation", runner_binary=worker, assessment_directory=context)
        with patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.root / "calls.json")):
            report = evaluation.run(self.root / "evaluation", max_new_attempts=20)
        self.assertEqual(len(json.loads((self.root / "calls.json").read_text())), 4)
        row = report["random"]["answers"][0]
        self.assertEqual(row["status"], "complete")
        self.assertEqual({key: value["value"] for key, value in row["scores"].items()},
                         dict(correctness=0, coverage=0))
        skipped = [case for case in row["checks"]["relationship"] if case["status"] == "skipped"]
        self.assertEqual(len(skipped), 3)
        self.assertEqual({case["skip_evidence"]["rule"] for case in skipped},
                         {"no_full_match", "unsupported_child"})
        self.assertTrue(all(case.get("parsed") is None and not case.get("qualification", {}).get("passed")
                            for case in skipped))
        self.assertEqual(report["summary"]["requests"]["totals"]["new"], 0)

    def test_trusted_uncovered_witness_stops_other_placement_calls(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        from sse_multivector import distillation_review_assessment as assessment
        teacher = subjects(("1", "Cables"), ("1.1", "Cable A"))
        student = subjects(("1", "Cables"), ("2", "Cable A"), ("3", "Other wording"))
        selected = self.selection([dict(note_id="validation-a", post="Cable A.",
            teacher=teacher, answer=answer(student))])
        context = self.root / "assessment"
        assessment.record(selected, "R01", context, teacher_meanings=[
            dict(teacher_numbers=["1"], required=False), dict(teacher_numbers=["1.1"], required=True)],
            reason="Independent complete source meaning.")
        evaluation.prepare(selected, self.root / "evaluation", runner_binary=self.worker(), assessment_directory=context)
        with patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.root / "calls.json")):
            report = evaluation.run(self.root / "evaluation", max_new_attempts=20)
        self.assertEqual(len(json.loads((self.root / "calls.json").read_text())), 2)
        row = report["random"]["answers"][0]
        self.assertEqual(row["scores"]["coverage"]["value"], 0)
        skipped = [case for case in row["checks"]["relationship"] if case["status"] == "skipped"]
        self.assertEqual(len(skipped), 1)
        self.assertEqual(skipped[0]["skip_evidence"]["rule"], "uncovered_compatible_heading")
        self.assertTrue(skipped[0]["skip_evidence"]["depends_on"])

    def test_first_semantic_uncovered_witness_stops_further_calls(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        from sse_multivector import distillation_review_assessment as assessment
        teacher = subjects(("1", "Cable A"))
        student = subjects(("1", "First other wording"), ("2", "Second other wording"),
                           ("3", "Cable A"), ("4", "Third other wording"))
        selected = self.selection([dict(note_id="validation-a", post="Cable A.",
            teacher=teacher, answer=answer(student))])
        context = self.root / "assessment"
        assessment.record(selected, "R01", context, teacher_meanings=[dict(teacher_numbers=["1"], required=True)],
                          reason="Independent complete source meaning.")
        evaluation.prepare(selected, self.root / "evaluation", runner_binary=self.worker(), assessment_directory=context)
        with patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.root / "calls.json")):
            report = evaluation.run(self.root / "evaluation", max_new_attempts=20)
        self.assertEqual(len(json.loads((self.root / "calls.json").read_text())), 7)
        row = report["random"]["answers"][0]
        self.assertEqual(row["scores"]["coverage"]["value"], 0)
        self.assertEqual(sum(case["status"] == "skipped" for case in row["checks"]["relationship"]), 2)
        self.assertEqual(row["qualification"]["status"], "pending")

    def test_matching_self_contradiction_is_checked_after_trusted_coverage_failure(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        from sse_multivector import distillation_review_assessment as assessment
        teacher = subjects(("1", "Cables"), ("1.1", "Cable A"))
        student = subjects(("1", "Cables"), ("2", "Paraphrase of Cable A"))
        selected = self.selection([dict(note_id="validation-a", post="Cable A.",
            teacher=teacher, answer=answer(student))])
        context = self.root / "assessment"
        assessment.record(selected, "R01", context, teacher_meanings=[
            dict(teacher_numbers=["1"], required=False), dict(teacher_numbers=["1.1"], required=True)],
            reason="Independent complete source meaning.")
        worker = self.worker()
        worker.write_text(worker.read_text().replace('{"teacher_id": None, "reason": "Fixture unmatched wording."}',
            '{"teacher_id": "T02", "reason": "Fixture full match."}').replace(
            'else {"valid": True, "reason": "Fixture semantic verdict."}',
            'else {"valid": not prompt.startswith("DSLv2"), "reason": "Fixture semantic verdict."}'))
        evaluation.prepare(selected, self.root / "evaluation", runner_binary=worker, assessment_directory=context)
        with patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.root / "calls.json")):
            report = evaluation.run(self.root / "evaluation", max_new_attempts=20)
        row = report["random"]["answers"][0]
        self.assertEqual(len(json.loads((self.root / "calls.json").read_text())), 3)
        self.assertEqual(row["status"], "inconsistent_verdicts")
        self.assertNotIn("scores", row)
        self.assertEqual(row["qualification"]["status"], "failed")
        self.assertEqual([case["parsed"]["valid"] for case in row["checks"]["relationship"]
                          if case["evidence"]["heading_number"] == "2"], [False])

    def test_covered_ancestors_skip_placements_but_retain_shared_actual_edge_requests(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        from sse_multivector import distillation_review_assessment as assessment
        teacher = subjects(("1", "Cable A"))
        student = subjects(("1", "New root"), ("1.1", "New parent"), ("1.1.1", "Cable A"))
        selected = self.selection([dict(note_id="validation-a", post="Cable A.",
            teacher=teacher, answer=answer(student))])
        context = self.root / "assessment"
        assessment.record(selected, "R01", context, teacher_meanings=[dict(teacher_numbers=["1"], required=True)],
                          reason="Independent complete source meaning.")
        evaluation.prepare(selected, self.root / "evaluation", runner_binary=self.worker(), assessment_directory=context)
        with patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.root / "calls.json")):
            report = evaluation.run(self.root / "evaluation", max_new_attempts=20)
        self.assertEqual(len(json.loads((self.root / "calls.json").read_text())), 6)
        row = report["random"]["answers"][0]
        self.assertEqual(row["scores"]["coverage"]["value"], 1)
        self.assertEqual(row["scores"]["correctness"]["value"], 1)
        self.assertTrue(all(case["status"] == "valid" for case in row["checks"]["relationship"]
                            if case["evidence"]["role"] == "actual_relationship"))
        skipped = [case for case in row["checks"]["relationship"] if case["status"] == "skipped"]
        self.assertEqual(len(skipped), 1)
        self.assertEqual(skipped[0]["skip_evidence"]["rule"], "match_beneath_heading")
        shared = [case for case in row["checks"]["relationship"]
                  if case["evidence"].get("heading_number") == "1.1"]
        self.assertEqual(shared[0]["status"], "valid")
        aliases = [case for case in row["checks"]["relationship"]
                   if case["input_sha256"] == shared[0]["input_sha256"]]
        self.assertEqual(sum(case["reused"] for case in aliases), 1)
        self.assertEqual(aliases[0]["parsed"], aliases[1]["parsed"])

    def test_no_positive_uncovered_witness_requires_every_remaining_placement(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        from sse_multivector import distillation_review_assessment as assessment
        teacher = subjects(("1", "Cable A"))
        student = subjects(("1", "First other wording"), ("2", "Second other wording"), ("3", "Cable A"))
        selected = self.selection([dict(note_id="validation-a", post="Cable A.",
            teacher=teacher, answer=answer(student))])
        context = self.root / "assessment"
        assessment.record(selected, "R01", context, teacher_meanings=[dict(teacher_numbers=["1"], required=True)],
                          reason="Independent complete source meaning.")
        worker = self.worker()
        worker.write_text(worker.read_text().replace('else {"valid": True, "reason": "Fixture semantic verdict."}',
            'else {"valid": not prompt.startswith("DSLv2"), "reason": "Fixture semantic verdict."}'))
        evaluation.prepare(selected, self.root / "evaluation", runner_binary=worker, assessment_directory=context)
        with patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.root / "calls.json")):
            report = evaluation.run(self.root / "evaluation", max_new_attempts=20)
        self.assertEqual(len(json.loads((self.root / "calls.json").read_text())), 6)
        row = report["random"]["answers"][0]
        self.assertEqual(row["scores"]["coverage"]["value"], 1)
        self.assertTrue(all(case["status"] == "valid" for case in row["checks"]["relationship"]))

    def test_zero_allowance_joins_saved_receipts_without_new_calls(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        selected, worker = self.selection(), self.worker()
        first, second = self.root / "first", self.root / "second"
        evaluation.prepare(selected, first, runner_binary=worker, history_root=self.root)
        with patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.root / "calls.json")):
            evaluation.run(first, max_new_attempts=10)
            evaluation.prepare(selected, second, runner_binary=worker, history_root=self.root)
            report = evaluation.run(second, max_new_attempts=0)
        self.assertEqual(len(json.loads((self.root / "calls.json").read_text())), 10)
        self.assertEqual(report["random"]["answers"][0]["status"], "complete")
        self.assertEqual(report["generation_usage"]["original_calls"], 10)
        self.assertEqual(report["summary"]["requests"]["totals"]["new"], 0)

    def test_cached_later_witness_is_reused_before_a_fresh_earlier_question(self):
        from experiment_runner import experiment
        from sse_multivector import distillation_review_evaluation as evaluation
        from sse_multivector import distillation_review_assessment as assessment
        teacher = subjects(("1", "Cable A"))
        student = subjects(("1", "Fresh first heading"), ("2", "Cached compatible heading"), ("3", "Cable A"))
        selected = self.selection([dict(note_id="validation-a", post="Cable A.",
            teacher=teacher, answer=answer(student))])
        context = self.root / "assessment"
        assessment.record(selected, "R01", context, teacher_meanings=[dict(teacher_numbers=["1"], required=True)],
                          reason="Independent complete source meaning.")
        first, second = self.root / "first", self.root / "second"
        prepared = evaluation.prepare(selected, first, runner_binary=self.worker(),
            history_root=self.root, assessment_directory=context)
        with patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.root / "calls.json")):
            for entry in prepared["experiments"]:
                if entry["check"] != "relationship":
                    experiment.run(Path(entry["path"]), 20)
                else:
                    rows = experiment.report(Path(entry["path"]), include_request_preview=False)["cases"]
                    cached = next(row["id"] for row in rows if row["evidence"]["heading_number"] == "2")
                    experiment.run(Path(entry["path"]), 1, only=[cached])
            self.assertEqual(len(json.loads((self.root / "calls.json").read_text())), 5)
            evaluation.prepare(selected, second, runner_binary=self.worker(),
                history_root=self.root, assessment_directory=context)
            report = evaluation.run(second, max_new_attempts=20)
        self.assertEqual(len(json.loads((self.root / "calls.json").read_text())), 5)
        row = report["random"]["answers"][0]
        self.assertEqual(row["scores"]["coverage"]["value"], 0)
        self.assertEqual(next(case["status"] for case in row["checks"]["relationship"]
                              if case["evidence"]["heading_number"] == "1"), "skipped")


if __name__ == "__main__":
    unittest.main()
