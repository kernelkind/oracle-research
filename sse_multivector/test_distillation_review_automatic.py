"""Automatic grading through the stable native CLI and saved worker receipts."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from sse_multivector import test_distillation_coverage_search as fixtures


PROJECT = Path(__file__).resolve().parents[1]
LAUNCHER = PROJECT.parent / "experiment-runner/bin/experiment-runner"


class DistillationAutomaticTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def native(self, *arguments, success=True, extra_env=None):
        result = subprocess.run([sys.executable, str(LAUNCHER), "--project-root", str(PROJECT),
            *map(str, arguments)], cwd=PROJECT,
            env=dict(os.environ, FAKE_RUNNER_LOG=str(self.root / "calls.json"), **(extra_env or {})),
            capture_output=True, text=True, timeout=45)
        if success:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def test_native_cli_exposes_prepare_and_single_run(self):
        prepared = self.native("prepare-distillation-automatic-grading", "--help")
        self.assertIn("--answer-id", prepared.stdout)
        self.assertIn("--verification-experiment", prepared.stdout)
        self.native("run-distillation-automatic-grading", "--help")

    def fixture(self, name):
        fixture = fixtures.DistillationCoverageSearchTests()
        fixture.root = self.root
        return fixture.collection_fixture(name, witness="2", policy="grading", audit_prerequisites=False)

    def test_native_run_completes_missing_witness_and_resume_adds_no_calls(self):
        _, _, coverage, original, _ = self.fixture("automatic-complete")
        frozen = (original / "run/results.jsonl").read_bytes()
        calls = (self.root / "calls.json").read_bytes()
        directory = self.root / "automatic"
        preparation = json.loads(self.native("prepare-distillation-automatic-grading", coverage,
            "--output", directory, "--runner-binary", self.root / "fake-runner").stdout)
        self.assertEqual(preparation["inference_calls"], 0)
        self.assertTrue(preparation["experiments"])
        self.assertEqual((self.root / "calls.json").read_bytes(), calls)
        result = json.loads(self.native("run-distillation-automatic-grading", directory).stdout)
        self.assertEqual(result["status"], "complete")
        report = json.loads(Path(result["report"]).read_text())
        self.assertEqual(report["automatic_status"], "complete")
        self.assertEqual(set(report["random"]["answers"][0]["scoring"]["scores"]), {"correctness", "coverage"})
        completed_calls = (self.root / "calls.json").read_bytes()
        resumed = json.loads(self.native("run-distillation-automatic-grading", directory).stdout)
        self.assertEqual(resumed["status"], "complete")
        self.assertEqual((self.root / "calls.json").read_bytes(), completed_calls)
        self.assertEqual((original / "run/results.jsonl").read_bytes(), frozen)

    def test_exhausted_worker_failure_fails_run_without_zero_grade_or_retry_loop(self):
        _, _, coverage, _, _ = self.fixture("automatic-failure")
        directory = self.root / "automatic-failure-run"
        self.native("prepare-distillation-automatic-grading", coverage, "--output", directory,
            "--runner-binary", self.root / "fake-runner")
        failed = self.native("run-distillation-automatic-grading", directory, success=False,
            extra_env={"FAKE_RUNNER_FAIL_STAGE": "prompt"})
        result = json.loads(failed.stdout)
        self.assertEqual(result["status"], "failed")
        calls = (self.root / "calls.json").read_bytes()
        self.native("run-distillation-automatic-grading", directory, success=False)
        self.assertEqual((self.root / "calls.json").read_bytes(), calls)
        self.assertFalse((directory / "grades.json").exists())

    def test_final_matching_is_fresh_xhigh_and_overrides_same_meaning_guard(self):
        from sse_multivector import distillation_coverage_search as coverage_module
        fixture = fixtures.DistillationCoverageSearchTests()
        fixture.root = self.root
        _, baseline, worker, _, native = fixture.path_baseline("automatic-final-match",
            edge_valid=False, required_subjects=("Cables", "Cable A"))
        coverage = self.root / "automatic-final-match-coverage"
        coverage_module.prepare(baseline, coverage, runner_binary=worker, policy="grading")
        original = Path(native["experiment"]) / "run/results.jsonl"
        frozen = original.read_bytes()
        count = len(json.loads((self.root / "calls.json").read_text()))
        directory = self.root / "automatic-final-match-run"
        preparation = json.loads(self.native("prepare-distillation-automatic-grading", coverage,
            "--output", directory, "--runner-binary", worker).stdout)
        self.assertEqual(len(preparation["experiments"]), 1)
        self.assertEqual(preparation["experiments"][0]["role"], "final_matching")
        result = json.loads(self.native("run-distillation-automatic-grading", directory).stdout)
        self.assertEqual(result["status"], "complete")
        calls = json.loads((self.root / "calls.json").read_text())
        self.assertEqual(len(calls) - count, 1)
        self.assertEqual(calls[-1]["request"]["reasoning"], "xhigh")
        self.assertEqual(original.read_bytes(), frozen)

    def test_all_independent_native_batches_start_before_waiting(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        from sse_multivector import distillation_review_assessment as assessment
        from sse_multivector import distillation_coverage_search as coverage_module
        from sse_multivector import test_distillation_review_evaluation as native_fixtures
        fixture = native_fixtures.DistillationReviewEvaluationTests()
        fixture.root = self.root
        teacher = native_fixtures.subjects(("1", "Cables"), ("1.1", "Cable A"))
        student = native_fixtures.subjects(("1", "Cables in general"), ("2", "Cable A"))
        selection = fixture.selection([dict(note_id="independent", post="Cable A.", teacher=teacher,
            answer=native_fixtures.answer(student))])
        worker = fixture.worker()
        response = ('(lambda payload: dict(evidence=[dict(student_number='
            'payload["candidates"][0]["student_number"], reason="Fixture candidate.")], '
            'witness_student_number=payload["candidates"][0]["student_number"]))'
            '(json.loads(prompt.strip().rsplit("\\n", 1)[-1]))')
        worker.write_text(worker.read_text().replace('{"teacher_id": None,', '{"teacher_id": "T01",').replace(
            '("DSMv3", "DSSv2", "DSLv2", "DSLv4")',
            '("DSMv3", "DSSv2", "DSLv2", "DSLv4", "DCSv1")').replace(
            'else {"valid": True, "reason": "Fixture semantic verdict."}',
            'else (' + response + ' if prompt.startswith("DCSv1") and \'"candidates":\' in prompt else '
            '{"valid": True, "reason": "Fixture semantic verdict."})'))
        context = self.root / "assessments"
        assessment.record(selection, "R01", context, teacher_meanings=[
            dict(teacher_numbers=["1"], required=True), dict(teacher_numbers=["1.1"], required=True)],
            reason="Complete trusted teacher meanings.")
        baseline = self.root / "baseline"
        prepared = evaluation.prepare(selection, baseline, runner_binary=worker, assessment_directory=context)
        for entry in prepared["experiments"]:
            if entry["check"] == "matching":
                fixture.native("run", entry["path"])
        coverage = self.root / "coverage"
        coverage_module.prepare(baseline, coverage, runner_binary=worker, policy="grading")
        directory = self.root / "automatic"
        prepared = json.loads(self.native("prepare-distillation-automatic-grading", coverage,
            "--output", directory, "--runner-binary", worker).stdout)
        self.assertGreaterEqual(len(prepared["experiments"]), 2)
        barrier = self.root / "barrier"
        barrier.mkdir()
        result = json.loads(self.native("run-distillation-automatic-grading", directory,
            extra_env={"FAKE_RUNNER_BARRIER": str(barrier),
                "FAKE_RUNNER_BARRIER_COUNT": str(len(prepared["experiments"]))}).stdout)
        self.assertEqual(result["status"], "complete")
