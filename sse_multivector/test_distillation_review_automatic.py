"""Automatic grading through the stable native CLI and saved worker receipts."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

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

    def test_fresh_evaluation_finishes_with_one_native_run_and_no_matrix(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        from sse_multivector import distillation_review_assessment as assessment
        from sse_multivector import test_distillation_review_evaluation as source_fixtures
        fixture = source_fixtures.DistillationReviewEvaluationTests()
        fixture.root = self.root
        selection = fixture.selection([dict(note_id="fresh-auto", post="Cable detail.",
            teacher=source_fixtures.subjects(("1", "Cable detail")),
            answer=source_fixtures.answer(source_fixtures.subjects(
                ("1", "Different cable"), ("1.1", "Different cable detail"))))])
        identifier = json.loads(selection.read_text())["random"]["answers"][0]["id"]
        context = self.root / "contexts"
        assessment.record(selection, identifier, context,
            teacher_meanings=[dict(teacher_numbers=["1"], required=True)],
            reason="Complete trusted fixture meaning.")
        worker = fixture.worker()
        source = self.root / "fresh-evaluation"
        evaluation.prepare(selection, source, assessment_directory=context,
            runner_binary=worker, actual_edges_only=True)
        directory = self.root / "fresh-automatic"
        preparation = json.loads(self.native("prepare-distillation-automatic-grading",
            "--evaluation", source, "--output", directory, "--runner-binary", worker).stdout)
        self.assertFalse((self.root / "calls.json").exists())
        self.assertEqual(preparation["inference_calls"], 0)
        result = json.loads(self.native("run-distillation-automatic-grading", directory).stdout)
        self.assertEqual(result["status"], "complete")
        grades = json.loads(Path(result["report"]).read_text())
        row = grades["random"]["answers"][0]
        self.assertEqual(row["scoring"]["scores"]["correctness"]["value"], 1)
        self.assertEqual(row["scoring"]["scores"]["coverage"]["value"], 0)
        calls = (self.root / "calls.json").read_bytes()
        self.native("run-distillation-automatic-grading", directory)
        self.assertEqual((self.root / "calls.json").read_bytes(), calls)
        for entry in evaluation.report(source)["experiments"]:
            self.assertTrue(all(row["status"] == "unrun" for row in entry["cases"]))

    def test_fresh_batches_preserve_eligible_shared_context_warming(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        from sse_multivector import distillation_review_assessment as assessment
        from sse_multivector import test_distillation_review_evaluation as source_fixtures
        fixture = source_fixtures.DistillationReviewEvaluationTests()
        fixture.root = self.root
        selection = fixture.selection([dict(note_id="fresh-cache", post="Cable detail. " * 600,
            teacher=source_fixtures.subjects(("1", "Cable detail")),
            answer=source_fixtures.answer(source_fixtures.subjects(
                ("1", "Different cable"), ("2", "Another cable"))))])
        identifier = json.loads(selection.read_text())["random"]["answers"][0]["id"]
        context = self.root / "contexts"
        assessment.record(selection, identifier, context,
            teacher_meanings=[dict(teacher_numbers=["1"], required=True)],
            reason="Complete trusted fixture meaning.")
        worker = fixture.worker()
        source = self.root / "fresh-evaluation"
        evaluation.prepare(selection, source, assessment_directory=context,
            runner_binary=worker, actual_edges_only=True)
        preparation = json.loads(self.native("prepare-distillation-automatic-grading",
            "--evaluation", source, "--output", self.root / "automatic",
            "--runner-binary", worker).stdout)
        matching = [entry for entry in preparation["experiments"]
            if entry["request_keys"][0][1] == "DSMv3"]
        self.assertEqual(len(matching), 1)
        self.assertTrue(matching[0]["prefix_cached"])
        self.assertFalse((self.root / "calls.json").exists())

    def fixture(self, name):
        fixture = fixtures.DistillationCoverageSearchTests()
        fixture.root = self.root
        return fixture.collection_fixture(name, witness="2", policy="grading", audit_prerequisites=False)

    def test_ready_batches_execute_before_first_collection(self):
        from sse_multivector import distillation_review_automatic as automatic
        _, _, coverage, _, _ = self.fixture("ready-before-collection")
        directory = self.root / "automatic"
        self.native("prepare-distillation-automatic-grading", coverage, "--output", directory,
            "--runner-binary", self.root / "fake-runner")
        native_collect = automatic._collect
        def collect_after_execution(destination, state, context):
            self.assertTrue(any(entry["status"] == "complete" for entry in state["experiments"]),
                "ready native work must execute before the first full collection")
            return native_collect(destination, state, context)
        with patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.root / "calls.json")):
            with patch.object(automatic, "_collect", side_effect=collect_after_execution):
                result = automatic.run(directory)
        self.assertEqual(result["status"], "complete")

    def test_changed_prepared_report_is_rejected_without_calls(self):
        _, _, coverage, _, _ = self.fixture("changed-prepared-report")
        directory = self.root / "automatic"
        preparation = json.loads(self.native("prepare-distillation-automatic-grading", coverage,
            "--output", directory, "--runner-binary", self.root / "fake-runner").stdout)
        report = Path(preparation["report"])
        report.write_bytes(report.read_bytes() + b"\n")
        calls = (self.root / "calls.json").read_bytes()
        failed = self.native("run-distillation-automatic-grading", directory, success=False)
        self.assertIn("automatic grading collection changed", failed.stderr)
        self.assertEqual((self.root / "calls.json").read_bytes(), calls)

    def test_native_process_crashes_retry_same_experiment_until_complete(self):
        from sse_multivector import distillation_review_automatic as automatic
        _, _, coverage, _, _ = self.fixture("retry-native-process")
        directory = self.root / "automatic"
        preparation = json.loads(self.native("prepare-distillation-automatic-grading", coverage,
            "--output", directory, "--runner-binary", self.root / "fake-runner").stdout)
        native_path = preparation["experiments"][0]["path"]
        prepared_manifest = (Path(native_path) / "experiment.json").read_bytes()
        subprocess_popen = subprocess.Popen
        starts = []
        class FailedProcess:
            pid = -1
            returncode = 1
            def poll(self):
                return self.returncode
            def wait(self):
                return self.returncode
        def crash_twice(arguments, **kwargs):
            if len(arguments) > 4 and arguments[1] == str(LAUNCHER) and arguments[4] == "run":
                starts.append(arguments)
                if len(starts) <= 2:
                    kwargs["stdout"].write("runner process terminated before writing a receipt\n")
                    return FailedProcess()
            return subprocess_popen(arguments, **kwargs)
        calls = len(json.loads((self.root / "calls.json").read_text()))
        with patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.root / "calls.json")):
            with patch.object(subprocess, "Popen", side_effect=crash_twice):
                result = automatic.run(directory)
        self.assertEqual(result["status"], "complete")
        self.assertEqual(len(starts), 3)
        self.assertTrue(all(arguments[5] == native_path for arguments in starts))
        self.assertEqual((Path(native_path) / "experiment.json").read_bytes(), prepared_manifest)
        self.assertEqual(len(json.loads((self.root / "calls.json").read_text())) - calls, 1)

    def test_permanent_failure_pauses_retrying_native_sibling(self):
        from sse_multivector import distillation_review_automatic as automatic
        _, _, coverage, _, _ = self.fixture("pause-retrying-sibling")
        directory = self.root / "automatic"
        preparation = json.loads(self.native("prepare-distillation-automatic-grading", coverage,
            "--output", directory, "--runner-binary", self.root / "fake-runner").stdout)
        original = preparation["experiments"][0]["path"]
        sibling = directory / "experiments/sibling"
        self.native("prepare", sibling, "--from", original, "--repeat")
        state_path = directory / "state.json"
        state = json.loads(state_path.read_text())
        state["experiments"].append(dict(state["experiments"][0], path=str(sibling)))
        state_path.write_text(json.dumps(state))
        subprocess_popen = subprocess.Popen
        class PermanentFailure:
            pid = -1
            returncode = 1
            def poll(self):
                return self.returncode if (sibling / "run/results.jsonl").exists() else None
            def wait(self):
                return self.returncode
        def fail_original(arguments, **kwargs):
            if len(arguments) > 5 and arguments[4:6] == ["run", original]:
                kwargs["stdout"].write("Experiment failed: malformed grader output\n")
                return PermanentFailure()
            return subprocess_popen(arguments, **kwargs)
        failures = json.dumps({"DSLv2": dict(attempts=1, error="Service temporarily unavailable",
            metadata=dict(http_status=503))})
        with patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.root / "calls.json"),
                FAKE_RUNNER_FAILURES=failures):
            with patch.object(subprocess, "Popen", side_effect=fail_original):
                result = automatic.run(directory)
        self.assertEqual(result["status"], "failed")
        native = json.loads(self.native("show", sibling, "--json").stdout)
        self.assertEqual(native["scheduling"]["state"], "paused")
        self.assertEqual(len((sibling / "run/results.jsonl").read_text().splitlines()), 1)

    def test_zero_call_completion_rechecks_saved_sources(self):
        fixture = fixtures.DistillationCoverageSearchTests()
        fixture.root = self.root
        _, _, coverage, original, _ = fixture.collection_fixture("zero-call", policy="grading",
            audit_prerequisites=False)
        directory = self.root / "automatic"
        preparation = json.loads(self.native("prepare-distillation-automatic-grading", coverage,
            "--output", directory).stdout)
        self.assertEqual(preparation["experiments"], [])
        source = original / "run/results.jsonl"
        source.write_bytes(source.read_bytes() + b"\n")
        calls = (self.root / "calls.json").read_bytes()
        result = json.loads(self.native("run-distillation-automatic-grading", directory, success=False).stdout)
        self.assertEqual(result["status"], "failed")
        self.assertIn("automatic grading collection source changed", result["error"])
        self.assertEqual((self.root / "calls.json").read_bytes(), calls)
        self.assertFalse((directory / "grades.json").exists())

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
