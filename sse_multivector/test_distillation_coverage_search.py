"""Focused coverage search through native production preparation and validation."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

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

    def test_native_cli_exposes_coverage_collection(self):
        project = Path(__file__).resolve().parents[1]
        launcher = project.parent / "experiment-runner/bin/experiment-runner"
        result = subprocess.run([sys.executable, str(launcher), "--project-root", str(project),
            "collect-distillation-coverage-search", "--help"], cwd=project,
            capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("--verification-experiment", result.stdout)
        self.assertIn("--premise-audit", result.stdout)

    def test_native_cli_prepares_medium_searches_without_running_premises(self):
        from sse_multivector import distillation_review_assessment as assessment
        from sse_multivector import distillation_review_evaluation as evaluation
        from sse_multivector import test_distillation_review_evaluation as fixtures
        fixture = fixtures.DistillationReviewEvaluationTests()
        fixture.root = self.root
        teacher = fixtures.subjects(("1", "Cable A"), ("2", "Cables"))
        selected = fixture.selection([dict(note_id="validation-a", post="Cable A.",
            teacher=teacher, answer=fixtures.answer(teacher))])
        context = self.root / "assessment"
        assessment.record(selected, "R01", context, teacher_meanings=[
            dict(teacher_numbers=["1"], required=True),
            dict(teacher_numbers=["2"], required=False)],
            reason="Exact matching premises; separate teacher roots have no trusted relationship.")
        baseline = self.root / "baseline"
        evaluation.prepare(selected, baseline, assessment_directory=context)
        frozen = (baseline / "evaluation.json").read_bytes()
        prepared = json.loads(fixture.native("prepare-distillation-coverage-search", baseline,
            "--output", self.root / "medium-search", "--reasoning-effort", "medium"))
        self.assertEqual(prepared["search_cases"], 1)
        self.assertEqual(prepared["inference_calls"], 0)
        for entry in prepared["experiments"]:
            report = json.loads(fixture.native("show", entry["path"], "--json"))
            self.assertEqual(report["settings"]["reasoning_effort"], "medium")
            self.assertEqual(report["prompt_id"], "DCSv1")
            self.assertEqual(report["cases"][0]["status"], "unrun")
        self.assertEqual((baseline / "evaluation.json").read_bytes(), frozen)
        self.assertFalse((self.root / "calls.json").exists())

    def test_bad_search_effort_is_rejected_before_creating_output(self):
        from sse_multivector import distillation_coverage_search as coverage
        destination = self.root / "invalid-effort"
        with self.assertRaisesRegex(ValueError, "reasoning_effort"):
            coverage.prepare(self.root / "missing-evaluation", destination, reasoning_effort="none")
        self.assertFalse(destination.exists())

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

    def test_exact_external_edge_disputes_retain_descendant_candidates(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        fixture, baseline, worker = self.baseline("edge-dispute", edge_valid=True)
        original = evaluation.report(baseline)
        edge = next(row for row in original["random"]["answers"][0]["checks"]["relationship"]
                    if row["evidence"]["role"] == "actual_relationship")
        for verdict in ("uncertain", "reject"):
            with self.subTest(verdict=verdict):
                audit = self.root / (verdict + "-edge-audit.jsonl")
                audit.write_text(json.dumps(dict(check="relationship", input_sha256=edge["input_sha256"],
                    output_sha256=hashlib.sha256(edge["output"].encode()).hexdigest(),
                    verdict=verdict, reason="This exact actual-edge output remains disputed.")) + "\n")
                prepared = json.loads(fixture.native("prepare-distillation-coverage-search", baseline,
                    "--output", self.root / (verdict + "-edge-coverage"), "--premise-audit", audit,
                    "--runner-binary", worker))
                native = json.loads(fixture.native("show", prepared["experiments"][0]["path"], "--json"))
                case = native["cases"][0]
                self.assertEqual(case["evidence"]["candidate_student_numbers"], ["1", "1.1"])
                self.assertEqual(case["evidence"]["omitted_descendants"], [])

    def test_external_edge_audits_require_matching_identity_and_complete_acceptance(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        fixture, baseline, worker = self.baseline("edge-audit-controls", edge_valid=True)
        original = evaluation.report(baseline)
        edge = next(row for row in original["random"]["answers"][0]["checks"]["relationship"]
                    if row["evidence"]["role"] == "actual_relationship")
        for name, overrides, expected in (
                ("accepted", dict(verdict="accept"), ["1"]),
                ("other-input", dict(input_sha256="0" * 64), ["1"]),
                ("other-output", dict(output_sha256="0" * 64), ["1"]),
                ("other-check", dict(check="support"), ["1"]),
                ("decision-error", dict(verdict="accept", decision_error=True), ["1", "1.1"]),
                ("explanation-error", dict(verdict="accept", explanation_error=True), ["1", "1.1"])):
            with self.subTest(name=name):
                row = dict(check="relationship", input_sha256=edge["input_sha256"],
                    output_sha256=hashlib.sha256(edge["output"].encode()).hexdigest(),
                    verdict="uncertain", reason="Complete source-bound actual-edge assessment.")
                row.update(overrides)
                audit = self.root / (name + "-edge-audit.jsonl")
                audit.write_text(json.dumps(row) + "\n")
                prepared = json.loads(fixture.native("prepare-distillation-coverage-search", baseline,
                    "--output", self.root / (name + "-edge-coverage"), "--premise-audit", audit,
                    "--runner-binary", worker))
                native = json.loads(fixture.native("show", prepared["experiments"][0]["path"], "--json"))
                self.assertEqual(native["cases"][0]["evidence"]["candidate_student_numbers"], expected)

    def test_native_frozen_search_rejects_changed_premise_snapshot(self):
        from sse_multivector import distillation_coverage_search as coverage
        fixture, baseline, worker = self.baseline("changed", edge_valid=True)
        prepared = coverage.prepare(baseline, self.root / "changed-coverage", runner_binary=worker)
        snapshot = baseline / "evaluation.json"
        snapshot.write_bytes(snapshot.read_bytes() + b"\n")
        plan = json.loads((Path(prepared["experiments"][0]["path"]) / "experiment.json").read_text())["plan"]
        with self.assertRaisesRegex(ValueError, "evaluation hash differs"):
            experiment_inputs.prepare_file(plan["dataset"], Path(plan["dataset"]["path"]), plan["prompt"]["text"])

    def test_snapshot_hashes_each_shared_receipt_file_once(self):
        from sse_multivector import distillation_coverage_search as coverage
        from sse_multivector import test_distillation_review_evaluation as fixtures
        _, baseline, _ = self.baseline("receipt-hashes", edge_valid=True,
            student=fixtures.subjects(("1", "Fruits"), ("1.1", "Cables"), ("1.2", "Cable bundles"), ("2", "Cable A")))
        reference = dict(path=str(baseline / "evaluation.json"), sha256=coverage.engine._sha256_file(baseline / "evaluation.json"))
        native_report = coverage.evaluation.report
        def report(*args, **kwargs):
            value = native_report(*args, **kwargs)
            hashing.reset_mock()  # Measure snapshot binding after the native report's own verification.
            return value
        with patch.object(coverage.engine, "_sha256_file", wraps=coverage.engine._sha256_file) as hashing:
            with patch.object(coverage.evaluation, "report", side_effect=report):
                original, _, protected = coverage._snapshot(reference, baseline)
        receipts = [Path(row["receipt"]["results_path"]) for native in original["experiments"]
                    for row in native["cases"] if row.get("receipt")]
        self.assertGreater(len(receipts), len(set(receipts)))
        files = set(receipts) | {path.parent / "manifest.json" for path in receipts}
        for path in files:
            with self.subTest(path=path.name):
                self.assertEqual(sum(Path(call.args[0]) == path for call in hashing.call_args_list), 1)
                self.assertEqual(protected[str(path)], coverage.engine._sha256_file(path))

    def test_native_preparation_derives_the_validated_source_only_once(self):
        from sse_multivector import distillation_coverage_search as coverage
        _, baseline, worker = self.baseline("single-source", edge_valid=True)
        with patch.object(coverage.evaluation, "report", wraps=coverage.evaluation.report) as reporting:
            with patch.object(coverage, "_cases", wraps=coverage._cases) as deriving:
                prepared = coverage.prepare(baseline, self.root / "single-source-coverage", runner_binary=worker)
        self.assertGreater(prepared["search_cases"], 0)
        self.assertEqual(reporting.call_count, 1)
        self.assertEqual(deriving.call_count, 1)

    def test_native_preparation_rejects_a_new_review_ledger_before_completion(self):
        from experiment_runner import experiment
        from sse_multivector import distillation_coverage_search as coverage
        _, baseline, worker = self.baseline("new-reviews", edge_valid=True)
        original = coverage.evaluation.report(baseline)
        ledger = Path(original["experiments"][0]["experiment"]) / "reviews.jsonl"
        self.assertFalse(ledger.exists())
        native_prepare = experiment.prepare
        def prepare(*args, **kwargs):
            value = native_prepare(*args, **kwargs)
            ledger.write_text("")
            return value
        with patch.object(experiment, "prepare", side_effect=prepare):
            with self.assertRaisesRegex(ValueError, "coverage premise changed while preparing"):
                coverage.prepare(baseline, self.root / "new-reviews-coverage", runner_binary=worker)

    def test_native_preparation_rejects_reviews_added_while_deriving_cases(self):
        from sse_multivector import distillation_coverage_search as coverage
        _, baseline, worker = self.baseline("reviews-during-cases", edge_valid=True)
        original = coverage.evaluation.report(baseline)
        ledger = Path(original["experiments"][0]["experiment"]) / "reviews.jsonl"
        native_cases = coverage._cases
        def cases(*args, **kwargs):
            value = native_cases(*args, **kwargs)
            ledger.write_text("")
            return value
        with patch.object(coverage, "_cases", side_effect=cases):
            with self.assertRaisesRegex(ValueError, "coverage premise changed while preparing"):
                coverage.prepare(baseline, self.root / "reviews-during-cases-coverage", runner_binary=worker)

    def test_snapshot_rejects_reviews_added_during_the_native_report(self):
        from sse_multivector import distillation_coverage_search as coverage
        _, baseline, worker = self.baseline("reviews-during-report", edge_valid=True)
        original = coverage.evaluation.report(baseline)
        ledger = Path(original["experiments"][0]["experiment"]) / "reviews.jsonl"
        native_report = coverage.evaluation.report
        def report(*args, **kwargs):
            value = native_report(*args, **kwargs)
            ledger.write_text("")
            return value
        with patch.object(coverage.evaluation, "report", side_effect=report):
            with self.assertRaisesRegex(ValueError, "coverage premise changed while preparing"):
                coverage.prepare(baseline, self.root / "reviews-during-report-coverage", runner_binary=worker)

    def test_native_preparation_rejects_a_new_result_ledger_for_an_unrun_source(self):
        from experiment_runner import experiment
        from sse_multivector import distillation_coverage_search as coverage
        _, baseline, worker = self.baseline("new-results")
        original = coverage.evaluation.report(baseline)
        results = next(Path(experiment.load(Path(row["experiment"]))[0]["run_directory"]) / "results.jsonl"
            for row in original["experiments"] if not (Path(row["experiment"]) / "run/results.jsonl").exists())
        self.assertFalse(results.exists())
        native_prepare = experiment.prepare
        def prepare(*args, **kwargs):
            value = native_prepare(*args, **kwargs)
            results.write_text("")
            return value
        with patch.object(experiment, "prepare", side_effect=prepare):
            with self.assertRaisesRegex(ValueError, "coverage premise changed while preparing"):
                coverage.prepare(baseline, self.root / "new-results-coverage", runner_binary=worker)

    def test_cached_source_keeps_exact_cases_and_rejects_removed_reviews(self):
        from experiment_runner import experiment
        from sse_multivector import distillation_coverage_search as coverage
        fixture, baseline, worker = self.baseline("removed-reviews", edge_valid=True)
        original = coverage.evaluation.report(baseline)
        native = next(row for row in original["experiments"] if any(
            case.get("origin") != "mechanical" and case["status"] == "valid" for case in row["cases"]))
        case = next(case for case in native["cases"] if case.get("origin") != "mechanical" and case["status"] == "valid")
        fixture.native("review", native["experiment"], "--case", case["id"], "--role", "agent",
            "--verdict", "accept", "--comment", "Complete native source assessment.")
        reference = dict(path=str(baseline / "evaluation.json"), sha256=coverage.engine._sha256_file(baseline / "evaluation.json"))
        source = dict(schema_version=1, evaluation=reference, answer_ids=[original["random"]["answers"][0]["id"]])
        context = {}
        cached = coverage.prepare_source(source, baseline, preparation_context=context)
        self.assertEqual(cached, coverage.prepare_source(source, baseline))
        self.assertEqual(cached, coverage.prepare_source(source, baseline, preparation_context=context))
        ledger = Path(native["experiment"]) / "reviews.jsonl"
        ledger.unlink()
        with self.assertRaisesRegex(ValueError, "coverage premise changed while preparing"):
            coverage.prepare_source(source, baseline, preparation_context=context)

    def test_native_preparation_rejects_receipt_changed_before_final_recheck(self):
        from experiment_runner import experiment
        from sse_multivector import distillation_coverage_search as coverage
        _, baseline, worker = self.baseline("receipt-changed", edge_valid=True)
        original = coverage.evaluation.report(baseline)
        results = next(Path(row["receipt"]["results_path"]) for native in original["experiments"]
                       for row in native["cases"] if row.get("receipt"))
        native_prepare = experiment.prepare
        def prepare(*args, **kwargs):
            value = native_prepare(*args, **kwargs)
            results.write_bytes(results.read_bytes() + b"\n")
            return value
        with patch.object(experiment, "prepare", side_effect=prepare):
            with self.assertRaisesRegex(ValueError, "coverage premise changed while preparing"):
                coverage.prepare(baseline, self.root / "receipt-changed-coverage", runner_binary=worker)

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

    def collection_fixture(self, name, *, witness=None, policy="audited", audit_prerequisites=True):
        from sse_multivector import distillation_coverage_search as coverage
        from sse_multivector import test_distillation_review_evaluation as fixtures
        teacher = fixtures.subjects(("1", "Fruits"), ("2", "Cable A"), ("3", "Vehicles"))
        student = fixtures.subjects(("1", "Fruits"), ("2", "Vehicles"), ("3", "Cable A"))
        if witness is not None:
            teacher = fixtures.subjects(("1", "Fruits"), ("2", "Cable A"))
            student = fixtures.subjects(("1", "Fruits"), ("2", "Cables"), ("3", "Cable A"))
        fixture, baseline, worker = self.baseline(name, teacher=teacher, student=student)
        from sse_multivector import distillation_review_evaluation as evaluation
        for group in evaluation.report(baseline)["experiments"]:
            for row in group["cases"]:
                if audit_prerequisites and row["status"] == "valid" and row.get("origin") != "mechanical":
                    fixture.native("review", group["experiment"], "--case", row["id"], "--role", "agent",
                        "--verdict", "accept", "--comment", "Complete source prerequisite independently audited.")
        result = dict(evidence=[dict(student_number=number, reason="Fixture complete candidate assessment.")
                               for number in ([witness] if witness else ["1", "2"])],
                      witness_student_number=witness)
        worker.write_text(worker.read_text().replace(
            '("DSMv3", "DSSv2", "DSLv2", "DSLv4")',
            '("DSMv3", "DSSv2", "DSLv2", "DSLv4", "DCSv1")').replace(
            'else {"valid": True, "reason": "Fixture semantic verdict."}',
            'else (' + repr(result) + ' if prompt.startswith("DCSv1") else '
            '{"valid": True, "reason": "Fixture semantic verdict."})'))
        output = self.root / (name + "-coverage")
        prepared = coverage.prepare(baseline, output, runner_binary=worker, policy=policy)
        native = Path(prepared["experiments"][0]["path"])
        fixture.native("run", native, "--max-new-attempts", 10)
        row = json.loads(fixture.native("show", native, "--json"))["cases"][0]
        return fixture, baseline, output, native, row

    def test_grading_policy_reuses_valid_native_checks_without_an_independent_accept(self):
        fixture, baseline, worker, _, _ = self.path_baseline("grading-path")
        prepared = json.loads(fixture.native("prepare-distillation-coverage-search", baseline,
            "--output", self.root / "grading-path-coverage", "--runner-binary", worker, "--policy", "grading"))
        self.assertEqual(prepared["policy"], "grading")
        self.assertEqual(prepared["search_cases"], 0)
        premise = prepared["preparation"]["settlements"][0]["compatibility_premise"]
        self.assertEqual(premise["reviews"], [])
        self.assertEqual(premise["audits"], [])

    def test_grading_policy_scores_native_verdicts_and_retains_uncertain_audit_diagnostics(self):
        fixture, _, output, native, row = self.collection_fixture("grading-null", policy="grading",
            audit_prerequisites=False)
        fixture.native("review", native, "--case", row["id"], "--role", "agent", "--verdict", "uncertain",
            "--comment", "Audit uncertainty is diagnostic, not a missing model decision.")
        result = json.loads(fixture.native("collect-distillation-coverage-search", output,
            "--output", self.root / "grading-null-collected.json"))
        self.assertEqual(result["policy"], "grading")
        answer = result["random"]["answers"][0]
        self.assertEqual(answer["scoring"]["status"], "valid")
        self.assertEqual(answer["scoring"]["scores"]["coverage"]["value"], 1)
        self.assertTrue(any(review["verdict"] == "uncertain" for premise in answer["premises"]
            for review in premise["reviews"]))

    def test_grading_policy_still_withholds_a_known_wrong_native_decision(self):
        fixture, _, output, native, row = self.collection_fixture("grading-reject", policy="grading",
            audit_prerequisites=False)
        fixture.native("review", native, "--case", row["id"], "--role", "agent", "--verdict", "reject",
            "--comment", "This saved model decision is known to be wrong.")
        result = json.loads(fixture.native("collect-distillation-coverage-search", output,
            "--output", self.root / "grading-reject-collected.json"))
        self.assertNotIn("coverage", result["random"]["answers"][0]["scoring"].get("scores", {}))

    def test_native_grade_comparison_uses_original_decisions_without_agent_intervention(self):
        from sse_multivector import distillation_coverage_search as coverage
        fixture, _, output, native, row = self.collection_fixture("automated-comparison", policy="grading",
            audit_prerequisites=False)
        fixture.native("review", native, "--case", row["id"], "--role", "agent", "--verdict", "reject",
            "--comment", "Audited error must remain diagnostic in the automated comparison.")
        correction = self.correction_search(fixture, native, row, "comparison-correction", witness="1")
        reference = self.root / "comparison-reference.json"
        coverage.collect(output, reference, correction_experiments=[correction])
        saved = {path: path.read_bytes() for path in (native / "reviews.jsonl", native / "run/results.jsonl", reference)}
        calls = (self.root / "calls.json").read_bytes()
        destination = self.root / "grade-comparison"
        summary = json.loads(fixture.native("compare-distillation-grades", output,
            "--reference", reference, "--output", destination))
        automated = json.loads((destination / "automated.json").read_text())
        answer = automated["random"]["answers"][0]
        self.assertEqual(answer["scoring"]["scores"]["coverage"]["value"], 1)
        self.assertTrue(automated["analysis_only"])
        self.assertEqual(summary["inference_calls"], 0)
        self.assertEqual(summary["random"]["metrics"]["coverage"]["paired_answers"], 0)
        self.assertEqual(summary["random"]["metrics"]["correctness"]["paired_answers"], 1)
        self.assertEqual(summary["random"]["statuses"]["reference"], {"pending": 1})
        self.assertEqual((self.root / "calls.json").read_bytes(), calls)
        self.assertTrue(all(path.read_bytes() == contents for path, contents in saved.items()))
        self.assertTrue(any(item["verdict"] == "reject" for item in summary["audit_diagnostics"]))

    def test_native_grade_comparison_measures_correction_impact_without_applying_it(self):
        from sse_multivector import distillation_coverage_search as coverage
        fixture, baseline, worker, group, row = self.adjudication_fixture("comparison-score-change")
        adjudication = self.root / "comparison-support-correction.json"
        fixture.native("adjudicate-distillation-review", group, "--case", row["id"],
            "--output", adjudication, "--valid", "false", "--classification", "incorrect",
            "--rule", "Judge what the post expresses, not whether its claims are true in the world.",
            "--reason", "The post does not express flying elephants on Mars.")
        output = self.root / "comparison-score-coverage"
        coverage.prepare(baseline, output, runner_binary=worker, policy="grading")
        reference = self.root / "comparison-score-reference.json"
        coverage.collect(output, reference, adjudications=[adjudication])
        summary = json.loads(fixture.native("compare-distillation-grades", output,
            "--reference", reference, "--output", self.root / "comparison-score-results"))
        pair = summary["paired_answers"]["random"][0]
        self.assertEqual(pair["automated_scores"]["correctness"]["value"], 1)
        self.assertAlmostEqual(pair["reference_scores"]["correctness"]["value"], 1 / 3)
        self.assertAlmostEqual(summary["random"]["metrics"]["correctness"]["mean_signed_change_percentage_points"], 200 / 3)
        self.assertEqual(summary["random"]["metrics"]["correctness"]["changed_answers"], 1)
        self.assertEqual(summary["challenge"]["metrics"]["coverage"]["paired_answers"], 0)
        self.assertIsNone(summary["challenge"]["metrics"]["coverage"]["mean_absolute_change_percentage_points"])

    def test_native_grade_comparison_reports_reference_uncertainty_separately(self):
        from sse_multivector import distillation_coverage_search as coverage
        fixture, baseline, worker, group, row = self.adjudication_fixture("comparison-uncertain")
        fixture.native("review", group, "--case", row["id"], "--role", "agent", "--verdict", "uncertain",
            "--comment", "Reference uncertainty is separate from a usable typed saved model verdict.")
        output = self.root / "comparison-uncertain-coverage"
        coverage.prepare(baseline, output, runner_binary=worker, policy="grading")
        reference = self.root / "comparison-uncertain-reference.json"
        coverage.collect(output, reference)
        summary = json.loads(fixture.native("compare-distillation-grades", output,
            "--reference", reference, "--output", self.root / "comparison-uncertain-results"))
        self.assertTrue(summary["paired_answers"]["random"][0]["reference_uncertainty"])
        self.assertEqual(summary["random"]["reference_uncertain_answers"], 1)
        self.assertEqual(summary["random"]["metrics"]["correctness"]["paired_answers"], 1)
        self.assertEqual(summary["random"]["metrics_without_uncertain_references"]["correctness"]["paired_answers"], 0)
        self.assertIsNone(summary["random"]["metrics_without_uncertain_references"]["correctness"]["mean_signed_change_percentage_points"])

    def test_grading_preserves_a_superseded_reject_without_treating_it_as_current(self):
        fixture, _, output, native, row = self.collection_fixture("grading-corrected-audit", policy="grading",
            audit_prerequisites=False)
        for verdict in ("reject", "uncertain"):
            fixture.native("review", native, "--case", row["id"], "--role", "agent", "--verdict", verdict,
                "--comment", "Later exact source assessment corrects the earlier mistaken audit.")
        result = json.loads(fixture.native("collect-distillation-coverage-search", output,
            "--output", self.root / "grading-corrected-audit.json"))
        answer = result["random"]["answers"][0]
        self.assertEqual(answer["scoring"]["status"], "valid")
        history = next(premise["reviews"] for premise in answer["premises"] if premise["case_id"] == row["id"])
        self.assertEqual([item["verdict"] for item in history], ["reject", "uncertain"])

    def correction_search(self, fixture, native, row, name, *, witness=None):
        original = dict(evidence=[dict(student_number=number, reason="Fixture complete candidate assessment.")
            for number in ["1", "2"]], witness_student_number=None)
        replacement = dict(evidence=[dict(student_number=number, reason="Corrected source-bound candidate assessment.")
            for number in ([witness] if witness else ["1", "2"])], witness_student_number=witness)
        worker = self.root / (name + "-worker")
        worker.write_text((self.root / "fake-runner").read_text().replace(repr(original), repr(replacement)))
        worker.chmod(0o755)
        destination = self.root / name
        fixture.native("prepare", destination, "--from", native, "--only", row["id"],
            "--runner-binary", worker, "--repeat")
        fixture.native("run", destination, "--max-new-attempts", 2)
        return destination

    def test_grading_uses_an_exact_selected_native_correction_and_preserves_the_original(self):
        fixture, _, output, native, row = self.collection_fixture("grading-correction", policy="grading",
            audit_prerequisites=False)
        fixture.native("review", native, "--case", row["id"], "--role", "agent", "--verdict", "reject",
            "--comment", "Known explanation error requires a new complete native output.")
        original = (native / "run/results.jsonl").read_bytes()
        correction = self.correction_search(fixture, native, row, "corrected-search")
        result = json.loads(fixture.native("collect-distillation-coverage-search", output,
            "--output", self.root / "grading-correction.json", "--correction-experiment", correction,
            "--correction-case", row["id"]))
        answer = result["random"]["answers"][0]
        self.assertEqual(answer["scoring"]["status"], "valid")
        proof = next(premise for premise in answer["premises"] if premise["case_id"] == row["id"])
        self.assertEqual(proof["correction"]["experiment"], str(correction))
        self.assertEqual(proof["correction"]["original_output_sha256"], hashlib.sha256(row["output"].encode()).hexdigest())
        self.assertEqual((native / "run/results.jsonl").read_bytes(), original)

    def test_grading_fills_an_unrun_native_check_without_inventing_an_original_output_hash(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        fixture, baseline, worker = self.baseline("unrun-correction")
        original = evaluation.report(baseline)
        pair = next(case for case in original["random"]["answers"][0]["checks"]["relationship"]
            if case["evidence"].get("teacher_numbers") == ["2"]
            and case["evidence"].get("heading_number") == "1.1")
        self.assertEqual(pair["status"], "unrun")
        self.assertIsNone(pair["output"])
        group = next(native["experiment"] for native in original["experiments"]
            if any(case["id"] == pair["id"] for case in native["cases"]))
        correction = self.root / "filled-unrun-native-check"
        fixture.native("prepare", correction, "--from", group, "--only", pair["id"], "--reasoning-effort", "high")
        fixture.native("run", correction, "--max-new-attempts", 2)
        prepared = json.loads(fixture.native("prepare-distillation-coverage-search", baseline,
            "--output", self.root / "filled-unrun-coverage", "--runner-binary", worker, "--policy", "grading",
            "--correction-experiment", correction, "--correction-case", pair["id"]))
        proof = prepared["preparation"]["settlements"][0]["compatibility_premise"]["correction"]
        self.assertEqual(proof["original_status"], "unrun")
        self.assertIsNone(proof["original_output_sha256"])
        self.assertIsNone(proof["original_receipt"])

    def test_native_correction_rejection_excludes_only_the_exact_held_verifier_output(self):
        from sse_multivector import distillation_coverage_search as coverage
        from sse_multivector import distillation_review_evaluation as evaluation
        fixture, baseline, output, _, _ = self.collection_fixture("rejected-held-verifier", witness="2",
            policy="grading", audit_prerequisites=False)
        original = evaluation.report(baseline)
        pair = next(row for row in original["random"]["answers"][0]["checks"]["relationship"]
            if row["evidence"].get("teacher_numbers") == ["2"]
            and row["evidence"].get("heading_number") == "2")
        group = next(native["experiment"] for native in original["experiments"]
            if any(row["id"] == pair["id"] for row in native["cases"]))
        false_worker = self.root / "historical-false-worker"
        false_worker.write_text((self.root / "fake-runner").read_text().replace(
            '{"valid": True, "reason": "Fixture semantic verdict."}',
            '{"valid": False, "reason": "Historical held interpretation."}'))
        false_worker.chmod(0o755)
        old = self.root / "old-held-verifier"
        fixture.native("prepare", old, "--from", group, "--only", pair["id"], "--reasoning-effort", "high",
            "--runner-binary", false_worker, "--history-root", self.root)
        fixture.native("run", old, "--max-new-attempts", 2)
        fixture.native("review", old, "--case", pair["id"], "--role", "agent", "--verdict", "uncertain",
            "--comment", "Historical FALSE complete output held for source interpretation.")
        fresh = self.root / "fresh-positive-verifier"
        fixture.native("prepare", fresh, "--from", group, "--only", pair["id"], "--reasoning-effort", "medium",
            "--runner-binary", self.root / "fake-runner", "--history-root", self.root)
        fixture.native("run", fresh, "--max-new-attempts", 2)
        pending = coverage.collect(output, self.root / "held-conflict.json", verification_experiments=[old, fresh])
        self.assertTrue(pending["random"]["answers"][0]["coverage_inconsistencies"])
        old_reviews = (old / "reviews.jsonl").read_bytes()
        correction = self.root / "source-reassessed-old-verifier"
        fixture.native("prepare", correction, "--from", old, "--only", pair["id"], "--history-root", self.root)
        fixture.native("run", correction, "--max-new-attempts", 2)
        self.assertEqual(json.loads(fixture.native("show", old, "--json"))["cases"][0]["output"],
            json.loads(fixture.native("show", correction, "--json"))["cases"][0]["output"])
        fixture.native("review", correction, "--case", pair["id"], "--role", "agent", "--verdict", "reject",
            "--comment", "Exact old FALSE output is now source-resolved as incorrect; TRUE is preserved.")
        result = coverage.collect(output, self.root / "held-resolved.json", verification_experiments=[old, fresh],
            correction_experiments=[correction])
        answer = result["random"]["answers"][0]
        self.assertFalse(answer["coverage_inconsistencies"])
        self.assertEqual(answer["scoring"]["scores"]["coverage"]["value"], 0)
        self.assertEqual((old / "reviews.jsonl").read_bytes(), old_reviews)

    def test_grading_rederives_changed_search_inputs_and_reuses_only_an_exact_native_donor(self):
        from sse_multivector import distillation_coverage_search as coverage
        from sse_multivector import distillation_review_evaluation as evaluation
        fixture, baseline, worker, pairs = self.negative_pair_fixture("rederived-search", ["1", "2"])
        output = self.root / "original-no-search"
        prepared = coverage.prepare(baseline, output, runner_binary=worker, policy="grading")
        self.assertEqual(prepared["search_cases"], 0)
        native = next(group["experiment"] for group in evaluation.report(baseline)["experiments"]
            if any(row["id"] == pairs["1"]["id"] for row in group["cases"]))
        rejection = self.root / "rejected-core-proof"
        fixture.native("prepare", rejection, "--from", native, "--only", pairs["1"]["id"])
        fixture.native("run", rejection, "--max-new-attempts", 2)
        fixture.native("review", rejection, "--case", pairs["1"]["id"], "--role", "agent", "--verdict", "reject",
            "--comment", "Old complete negative output has an incorrect explanation; derive a new search.")
        donor_worker = self.root / "rederived-donor-worker"
        donor_result = dict(evidence=[dict(student_number="1", reason="Independent complete negative search.")],
            witness_student_number=None)
        donor_worker.write_text(worker.read_text().replace('("DSMv3", "DSSv2", "DSLv2", "DSLv4")',
            '("DSMv3", "DSSv2", "DSLv2", "DSLv4", "DCSv1")').replace(
            'else {"valid": not prompt.startswith("DSLv2"), "reason": "Fixture semantic verdict."}',
            'else (' + repr(donor_result) + ' if prompt.startswith("DCSv1") else '
            '{"valid": not prompt.startswith("DSLv2"), "reason": "Fixture semantic verdict."})'))
        donor_worker.chmod(0o755)
        donor = coverage.prepare(baseline, self.root / "current-derived-donor", runner_binary=donor_worker,
            policy="grading", correction_experiments=[rejection])
        self.assertEqual(donor["search_cases"], 1)
        search = Path(donor["experiments"][0]["path"])
        fixture.native("run", search, "--max-new-attempts", 2)
        missing = coverage.collect(output, self.root / "missing-derived-search.json", correction_experiments=[rejection])
        self.assertNotIn("coverage", missing["random"]["answers"][0]["scoring"].get("scores", {}))
        result = coverage.collect(output, self.root / "exact-derived-search.json", correction_experiments=[rejection, search])
        self.assertEqual(result["random"]["answers"][0]["scoring"]["scores"]["coverage"]["value"], 1)

    def test_grading_reuses_a_negative_search_for_an_identical_candidate_subset(self):
        from sse_multivector import distillation_coverage_search as coverage
        from sse_multivector import distillation_review_evaluation as evaluation
        from sse_multivector import test_distillation_review_evaluation as fixtures
        fixture, baseline, worker = self.baseline("negative-subset", student=fixtures.subjects(
            ("1", "Fruit varieties"), ("1.1", "Apples"), ("2", "Cable A")))
        response = dict(evidence=[dict(student_number=number, reason="Fruit restrictions are absent.")
            for number in ["1", "1.1"]], witness_student_number=None)
        search_worker = self.root / "subset-search-worker"
        search_worker.write_text(worker.read_text().replace('("DSMv3", "DSSv2", "DSLv2", "DSLv4")',
            '("DSMv3", "DSSv2", "DSLv2", "DSLv4", "DCSv1")').replace(
            'else {"valid": True, "reason": "Fixture semantic verdict."}',
            'else (' + repr(response) + ' if prompt.startswith("DCSv1") else '
            '{"valid": True, "reason": "Fixture semantic verdict."})'))
        search_worker.chmod(0o755)
        output = self.root / "negative-subset-coverage"
        prepared = coverage.prepare(baseline, output, runner_binary=search_worker, policy="grading")
        search = Path(prepared["experiments"][0]["path"])
        fixture.native("run", search, "--max-new-attempts", 2)
        original = json.loads(fixture.native("show", search, "--json"))["cases"][0]
        self.assertEqual(original["evidence"]["candidate_student_numbers"], ["1", "1.1"])
        native = evaluation.report(baseline)
        edge = next(row for row in native["random"]["answers"][0]["checks"]["relationship"]
            if row["evidence"].get("role") == "actual_relationship")
        group = next(row["experiment"] for row in native["experiments"]
            if any(case["id"] == edge["id"] and case["evidence"]["check"] == "relationship"
                   for case in row["cases"]))
        correction = self.root / "now-valid-actual-edge"
        fixture.native("prepare", correction, "--from", group, "--only", edge["id"], "--reasoning-effort", "high")
        fixture.native("run", correction, "--max-new-attempts", 2)
        result = coverage.collect(output, self.root / "negative-subset-collected.json", correction_experiments=[correction])
        answer = result["random"]["answers"][0]
        self.assertEqual(answer["scoring"]["scores"]["coverage"]["value"], 1)
        proof = next(row for row in answer["premises"] if "coverage_subset" in row)
        self.assertEqual(proof["input_sha256"], original["input_sha256"])
        self.assertEqual(proof["receipt"], original["receipt"])
        self.assertEqual(proof["coverage_subset"]["retained_student_numbers"], ["1"])
        self.assertEqual(proof["coverage_subset"]["removed_student_numbers"], ["1.1"])
        template = (Path(__file__).parent / "distillation-review-v1/coverage-search-prompt-v1.md").read_text()
        current = dict(original, inputs=proof["coverage_subset"]["current_inputs"])
        for change in ("expanded", "post", "teacher", "contexts"):
            with self.subTest(change=change):
                altered = dict(current, inputs=dict(current["inputs"]))
                payload = json.loads(altered["inputs"]["COVERAGE_INPUT"])
                if change == "expanded":
                    payload["candidates"].append(dict(payload["candidates"][0], student_number="99"))
                elif change == "post":
                    altered["inputs"]["POST"] += " Different source context."
                elif change == "teacher":
                    payload["teacher_subject"] = "Different teacher meaning"
                else:
                    payload["candidates"][0]["teacher_contexts"] = []
                altered["inputs"]["COVERAGE_INPUT"] = json.dumps(payload)
                self.assertIsNone(coverage._negative_subset(altered, [original], {}, template))
        positive = dict(original, parsed=dict(original["parsed"], witness_student_number="1"))
        self.assertIsNone(coverage._negative_subset(current, [positive], {}, template))
        fixture.native("review", search, "--case", original["id"], "--role", "agent", "--verdict", "reject",
            "--comment", "Rejected complete source decision cannot justify any derived subset.")
        rejected = json.loads(fixture.native("show", search, "--json"))["cases"][0]
        self.assertIsNone(coverage._negative_subset(current, [rejected], {}, template))

    def adjudication_fixture(self, name):
        from sse_multivector import distillation_review_evaluation as evaluation
        from sse_multivector import test_distillation_review_evaluation as fixtures
        fixture, baseline, worker = self.baseline(name, student=fixtures.subjects(
            ("1", "Fruits"), ("2", "Flying elephants on Mars"), ("2.1", "Flying elephants on Mars")))
        report = evaluation.report(baseline)
        group = next(row for row in report["experiments"] if row["cases"][0]["evidence"]["check"] == "support")
        row = next(row for row in group["cases"] if row["evidence"]["student_number"] == "2")
        return fixture, baseline, worker, group["experiment"], row

    def test_native_adjudication_grades_identical_aliases_without_rewriting_provider_outputs(self):
        from sse_multivector import distillation_coverage_search as coverage
        fixture, baseline, worker, group, row = self.adjudication_fixture("source-adjudication")
        receipt = Path(row["receipt"]["results_path"])
        original = receipt.read_bytes()
        adjudication = self.root / "unsupported-subject-adjudication.json"
        record = json.loads(fixture.native("adjudicate-distillation-review", group, "--case", row["id"],
            "--output", adjudication, "--valid", "false", "--classification", "incorrect",
            "--rule", "Judge what the post expresses, not whether its claims are true in the world.",
            "--reason", "The complete original post mentions Cable A and fruit; it never expresses flying elephants on Mars."))
        self.assertEqual(record["actor"], "agent")
        self.assertEqual(record["decision"]["valid"], False)
        self.assertEqual(record["original"]["receipt"], row["receipt"])
        output = self.root / "source-adjudication-coverage"
        coverage.prepare(baseline, output, runner_binary=worker, policy="grading")
        result = json.loads(fixture.native("collect-distillation-coverage-search", output,
            "--output", self.root / "source-adjudication-grades.json", "--adjudication", adjudication))
        answer = result["random"]["answers"][0]
        self.assertEqual(answer["scoring"]["findings"]["incorrect_subjects"], ["2", "2.1"])
        adjudicated = [proof for proof in answer["premises"] if proof["origin"] == "adjudicated"]
        self.assertEqual(len(adjudicated), 2)
        self.assertTrue(all(proof["receipt"] is None for proof in adjudicated))
        self.assertTrue(all(proof["adjudication"]["actor"] == "agent" for proof in adjudicated))
        self.assertEqual(receipt.read_bytes(), original)
        overwritten = subprocess.run([sys.executable, str(Path(__file__).resolve().parents[2] /
            "experiment-runner/bin/experiment-runner"), "--project-root", str(Path(__file__).resolve().parents[1]),
            "adjudicate-distillation-review", group, "--case", row["id"], "--output", str(adjudication),
            "--valid", "false", "--classification", "incorrect", "--rule", "Judge what the post expresses, not whether its claims are true in the world.",
            "--reason", "Repeated immutable write."], capture_output=True, text=True)
        self.assertNotEqual(overwritten.returncode, 0)
        self.assertIn("already exists", overwritten.stderr)

    def test_native_adjudication_refuses_a_verdict_of_the_wrong_check_type(self):
        fixture, _, _, group, row = self.adjudication_fixture("wrong-adjudication-type")
        destination = self.root / "wrong-type.json"
        result = subprocess.run([sys.executable, str(Path(__file__).resolve().parents[2] /
            "experiment-runner/bin/experiment-runner"), "--project-root", str(Path(__file__).resolve().parents[1]),
            "adjudicate-distillation-review", group, "--case", row["id"], "--output", str(destination),
            "--teacher-id", "null", "--classification", "incorrect", "--rule", "Judge what the post expresses, not whether its claims are true in the world.",
            "--reason", "Wrong verdict shape must be rejected."], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("support", result.stderr)
        self.assertFalse(destination.exists())

    def test_native_unresolved_adjudication_withholds_a_grade_and_reports_alias_counts(self):
        from sse_multivector import distillation_coverage_search as coverage
        fixture, baseline, worker, group, row = self.adjudication_fixture("uncertain-source-adjudication")
        path = self.root / "unresolved-source.json"
        recorded = json.loads(fixture.native("adjudicate-distillation-review", group, "--case", row["id"],
            "--output", path, "--classification", "uncertain",
            "--rule", "Judge what the post expresses, not whether its claims are true in the world.",
            "--reason", "Source interpretation remains unresolved; no semantic verdict is being supplied."))
        self.assertIsNone(recorded["decision"])
        output = self.root / "unresolved-source-coverage"
        coverage.prepare(baseline, output, runner_binary=worker, policy="grading")
        result = coverage.collect(output, self.root / "unresolved-source-grades.json", adjudications=[path])
        self.assertEqual(result["random"]["answers"][0]["scoring"]["status"], "pending")
        summary = result["adjudication_summary"]
        self.assertEqual(summary["unresolved_questions"], 1)
        self.assertEqual(summary["affected_occurrences"], 2)
        self.assertEqual(summary["affected_answers"], 1)
        self.assertEqual(summary["original_decision_classifications"]["uncertain"], 1)

    def test_conflicting_native_adjudications_remain_pending(self):
        from sse_multivector import distillation_coverage_search as coverage
        fixture, baseline, worker, group, row = self.adjudication_fixture("conflicting-source-adjudications")
        paths = []
        for value, classification in (("false", "incorrect"), ("true", "correct")):
            path = self.root / (value + "-source.json")
            fixture.native("adjudicate-distillation-review", group, "--case", row["id"], "--output", path,
                "--valid", value, "--classification", classification,
                "--rule", "Judge what the post expresses, not whether its claims are true in the world.",
                "--reason", "Explicit conflicting source assessment retained as a separate immutable record.")
            paths.append(path)
        output = self.root / "conflicting-source-coverage"
        coverage.prepare(baseline, output, runner_binary=worker, policy="grading")
        result = coverage.collect(output, self.root / "conflicting-source-grades.json", adjudications=paths)
        self.assertEqual(result["random"]["answers"][0]["scoring"]["status"], "pending")
        self.assertEqual(result["adjudication_summary"]["unresolved_questions"], 1)

    def test_native_same_verdict_adjudication_corrects_a_mistaken_rejection(self):
        from sse_multivector import distillation_coverage_search as coverage
        from sse_multivector import distillation_review_evaluation as evaluation
        fixture, baseline, worker, parent, matching_group = self.path_baseline("correct-source-adjudication")
        fixture.native("review", matching_group["experiment"], "--case", parent["id"], "--role", "agent",
            "--verdict", "reject", "--comment", "Mistaken old matching audit retained as history.")
        record = self.root / "correct-matching-source.json"
        fixture.native("adjudicate-distillation-review", matching_group["experiment"], "--case", parent["id"],
            "--output", record, "--teacher-id", parent["parsed"]["teacher_id"], "--classification", "correct",
            "--rule", "The teacher wording is authoritative.", "--reason", parent["parsed"]["reason"])
        output = self.root / "correct-source-coverage"
        coverage.prepare(baseline, output, runner_binary=worker, policy="grading")
        result = coverage.collect(output, self.root / "correct-source-grades.json", adjudications=[record])
        answer = result["random"]["answers"][0]
        self.assertEqual(answer["scoring"]["status"], "valid")
        proof = next(row for row in answer["premises"] if row["case_id"] == parent["id"]
            and row["input_sha256"] == parent["input_sha256"])
        self.assertEqual(proof["origin"], "adjudicated")
        self.assertEqual(proof["adjudication"]["original_decision_classification"], "correct")
        self.assertEqual(evaluation.report(baseline)["random"]["answers"][0]["checks"]["matching"][0]["output"], parent["output"])

    def test_grading_does_not_choose_between_contradictory_native_corrections(self):
        from sse_multivector import distillation_coverage_search as coverage
        fixture, _, output, native, row = self.collection_fixture("grading-conflict", policy="grading",
            audit_prerequisites=False)
        fixture.native("review", native, "--case", row["id"], "--role", "agent", "--verdict", "reject",
            "--comment", "Saved output rejected before conflicting fallback draws.")
        corrections = [self.correction_search(fixture, native, row, "negative-correction"),
            self.correction_search(fixture, native, row, "positive-correction", witness="1")]
        result = coverage.collect(output, self.root / "grading-conflict.json", correction_experiments=corrections)
        answer = result["random"]["answers"][0]
        self.assertNotIn("coverage", answer["scoring"].get("scores", {}))
        self.assertTrue(any(dependency["decision_conflicts"] for dependency in answer["dependencies"]
            if "decision_conflicts" in dependency))

    def test_native_collector_scores_only_accepted_complete_search_outputs(self):
        fixture, _, output, native, row = self.collection_fixture("collect-null")
        fixture.native("review", native, "--case", row["id"], "--role", "agent",
            "--verdict", "accept", "--comment", "Complete null output independently audited.")
        destination = self.root / "collected.json"
        result = json.loads(fixture.native("collect-distillation-coverage-search", output,
            "--output", destination))
        answer = result["random"]["answers"][0]
        self.assertEqual(answer["scoring"]["status"], "valid")
        self.assertEqual(answer["scoring"]["scores"]["coverage"]["value"], 1)
        self.assertEqual(answer["scoring"]["scores"]["correctness"]["value"], 1)
        self.assertEqual(result, json.loads(destination.read_text()))

    def test_unaudited_rejected_and_uncertain_search_outputs_remain_ungraded(self):
        from sse_multivector import distillation_coverage_search as coverage
        fixture, _, output, native, row = self.collection_fixture("ungraded-null")
        for verdict in (None, "reject", "uncertain"):
            with self.subTest(verdict=verdict):
                if verdict:
                    fixture.native("review", native, "--case", row["id"], "--role", "agent",
                        "--verdict", verdict, "--comment", "This complete search output is not accepted.")
                result = coverage.collect(output, self.root / (str(verdict) + "-collected.json"))
                answer = result["random"]["answers"][0]
                self.assertEqual(answer["scoring"]["status"], "pending")
                self.assertNotIn("coverage", answer["scoring"].get("scores", {}))
                self.assertTrue(answer["dependencies"])

    def test_positive_search_needs_exact_accepted_native_verification(self):
        from sse_multivector import distillation_coverage_search as coverage
        from sse_multivector import distillation_review_evaluation as evaluation
        fixture, baseline, output, native, row = self.collection_fixture("collect-positive", witness="2")
        fixture.native("review", native, "--case", row["id"], "--role", "agent",
            "--verdict", "accept", "--comment", "Complete positive search independently audited.")
        pending = coverage.collect(output, self.root / "positive-pending.json")
        self.assertNotIn("coverage", pending["random"]["answers"][0]["scoring"].get("scores", {}))
        original = evaluation.report(baseline)
        pair = next(case for case in original["random"]["answers"][0]["checks"]["relationship"]
                    if case["evidence"].get("teacher_numbers") == ["2"]
                    and case["evidence"].get("heading_number") == "2")
        source = next(group["experiment"] for group in original["experiments"]
                      if any(case["id"] == pair["id"] for case in group["cases"]))
        verification = self.root / "positive-verification"
        fixture.native("prepare", verification, "--from", source, "--only", pair["id"], "--reasoning-effort", "high")
        fixture.native("run", verification, "--max-new-attempts", 2)
        unreviewed = coverage.collect(output, self.root / "unreviewed-positive.json",
            verification_experiments=[verification])
        self.assertNotIn("coverage", unreviewed["random"]["answers"][0]["scoring"].get("scores", {}))
        fixture.native("review", verification, "--case", pair["id"], "--role", "agent",
            "--verdict", "accept", "--comment", "Exact complete positive pair independently audited.")
        result = coverage.collect(output, self.root / "positive-collected.json", verification_experiments=[verification])
        self.assertEqual(result["random"]["answers"][0]["scoring"]["scores"]["coverage"]["value"], 0)

    def test_collector_requires_exact_external_search_output_hash(self):
        from sse_multivector import distillation_coverage_search as coverage
        _, _, output, _, row = self.collection_fixture("external-collection")
        for label, digest in (("wrong", "0" * 64), ("exact", hashlib.sha256(row["output"].encode()).hexdigest())):
            audit = self.root / (label + "-collection-audit.jsonl")
            audit.write_text(json.dumps(dict(check="coverage_search", input_sha256=row["input_sha256"],
                output_sha256=digest, verdict="accept", reason="Complete exact search assessment.")) + "\n")
            result = coverage.collect(output, self.root / (label + "-external-collected.json"), premise_audits=[audit])
            scores = result["random"]["answers"][0]["scoring"].get("scores", {})
            self.assertEqual("coverage" in scores, label == "exact")

    def test_collector_rejects_a_changed_frozen_source_ledger(self):
        from sse_multivector import distillation_coverage_search as coverage
        from sse_multivector import distillation_review_evaluation as evaluation
        _, baseline, output, _, _ = self.collection_fixture("collection-integrity", witness="2")
        original = evaluation.report(baseline)
        ledger = next(Path(case["receipt"]["results_path"]) for group in original["experiments"]
                      for case in group["cases"] if case.get("receipt"))
        ledger.write_bytes(ledger.read_bytes() + b"\n")
        destination = self.root / "changed-source-collected.json"
        with self.assertRaisesRegex(ValueError, "coverage collection source changed"):
            coverage.collect(output, destination)
        self.assertFalse(destination.exists())

    def test_accepted_exact_uncovered_pair_is_settled_before_search(self):
        from sse_multivector import distillation_coverage_search as coverage
        from sse_multivector import distillation_review_evaluation as evaluation
        fixture, baseline, worker = self.baseline("accepted-pair", edge_valid=True)
        original = evaluation.report(baseline)
        pair = next(row for row in original["random"]["answers"][0]["checks"]["relationship"]
                    if row["evidence"].get("teacher_numbers") == ["2"]
                    and row["evidence"].get("heading_number") == "1.1")
        group = next(native for native in original["experiments"]
                     if any(case["id"] == pair["id"] for case in native["cases"]))
        fixture.native("review", group["experiment"], "--case", pair["id"], "--role", "agent",
            "--verdict", "accept", "--comment", "Complete compatible pair independently audited.")
        result = coverage.prepare(baseline, self.root / "accepted-pair-coverage", runner_binary=worker)
        self.assertEqual(result["search_cases"], 0)
        settlement = result["preparation"]["settlements"][0]
        self.assertEqual(settlement["rule"], "accepted_uncovered_compatible_heading")
        self.assertEqual(settlement["compatibility_premise"]["case_id"], pair["id"])

    def test_collection_withdraws_a_settlement_when_its_exact_premise_is_disputed(self):
        from sse_multivector import distillation_coverage_search as coverage
        from sse_multivector import distillation_review_evaluation as evaluation
        fixture, baseline, worker = self.baseline("withdraw-pair", edge_valid=True)
        original = evaluation.report(baseline)
        pair = next(row for row in original["random"]["answers"][0]["checks"]["relationship"]
                    if row["evidence"].get("teacher_numbers") == ["2"]
                    and row["evidence"].get("heading_number") == "1.1")
        for group in original["experiments"]:
            for row in group["cases"]:
                if row["id"] == pair["id"] or (row["evidence"]["check"] == "matching" and row["status"] == "valid"):
                    fixture.native("review", group["experiment"], "--case", row["id"], "--role", "agent",
                        "--verdict", "accept", "--comment", "Complete source premise independently audited.")
        output = self.root / "withdraw-pair-coverage"
        prepared = coverage.prepare(baseline, output, runner_binary=worker)
        self.assertEqual(prepared["search_cases"], 0)
        audit = self.root / "withdraw-exact-pair.jsonl"
        audit.write_text(json.dumps(dict(check="relationship", input_sha256=pair["input_sha256"],
            output_sha256=hashlib.sha256(pair["output"].encode()).hexdigest(), verdict="uncertain",
            reason="The exact complete pair interpretation remains disputed.")) + "\n")
        result = coverage.collect(output, self.root / "withdraw-pair-collected.json", premise_audits=[audit])
        self.assertNotIn("coverage", result["random"]["answers"][0]["scoring"].get("scores", {}))

    def negative_pair_fixture(self, name, accepted_numbers):
        from sse_multivector import distillation_review_evaluation as evaluation
        from sse_multivector import test_distillation_review_evaluation as fixtures
        fixture, baseline, worker = self.baseline(name, edge_valid=False,
            teacher=fixtures.subjects(("1", "Fruits"), ("2", "Cable A"), ("3", "Vehicles")),
            student=fixtures.subjects(("1", "Fruits"), ("2", "Vehicles"), ("3", "Cable A")))
        pairs = {}
        for group in evaluation.report(baseline)["experiments"]:
            for row in group["cases"]:
                if (row["evidence"].get("teacher_numbers") == ["2"]
                        and row["evidence"].get("heading_number") in accepted_numbers):
                    self.assertFalse(row["parsed"]["valid"])
                    pairs[row["evidence"]["heading_number"]] = row
                    fixture.native("review", group["experiment"], "--case", row["id"], "--role", "agent",
                        "--verdict", "accept", "--comment", "Complete exact negative pair independently audited.")
        return fixture, baseline, worker, pairs

    def test_accepted_negative_pairs_are_removed_before_search_with_bound_proofs(self):
        from sse_multivector import distillation_coverage_search as coverage
        fixture, baseline, worker, pairs = self.negative_pair_fixture("negative-candidate", ["1"])
        prepared = coverage.prepare(baseline, self.root / "negative-candidate-coverage", runner_binary=worker)
        native = json.loads(fixture.native("show", prepared["experiments"][0]["path"], "--json"))
        case = native["cases"][0]
        self.assertEqual(case["evidence"]["candidate_student_numbers"], ["2"])
        excluded = case["evidence"]["excluded_incompatible_candidates"]
        self.assertEqual([row["student_number"] for row in excluded], ["1"])
        self.assertEqual(excluded[0]["compatibility_premise"]["case_id"], pairs["1"]["id"])

    def test_all_accepted_negative_roots_settle_and_withdrawals_keep_coverage_pending(self):
        from sse_multivector import distillation_coverage_search as coverage
        _, baseline, worker, pairs = self.negative_pair_fixture("negative-settlement", ["1", "2"])
        output = self.root / "negative-settlement-coverage"
        prepared = coverage.prepare(baseline, output, runner_binary=worker)
        self.assertEqual(prepared["search_cases"], 0)
        self.assertEqual(prepared["preparation"]["settlements"][0]["rule"], "accepted_uncovered_incompatible_headings")
        result = coverage.collect(output, self.root / "negative-settled-collected.json")
        self.assertEqual(result["random"]["answers"][0]["scoring"]["scores"]["coverage"]["value"], 1)
        audit = self.root / "withdraw-negative-pair.jsonl"
        pair = pairs["2"]
        audit.write_text(json.dumps(dict(check="relationship", input_sha256=pair["input_sha256"],
            output_sha256=hashlib.sha256(pair["output"].encode()).hexdigest(), verdict="uncertain",
            reason="The exact negative interpretation is now unresolved.")) + "\n")
        pending = coverage.collect(output, self.root / "negative-withdrawn-collected.json", premise_audits=[audit])
        self.assertNotIn("coverage", pending["random"]["answers"][0]["scoring"].get("scores", {}))

    def test_accepted_null_cannot_overwrite_an_accepted_exact_positive_pair(self):
        from sse_multivector import distillation_coverage_search as coverage
        from sse_multivector import distillation_review_evaluation as evaluation
        fixture, baseline, output, native, row = self.collection_fixture("null-contradiction")
        fixture.native("review", native, "--case", row["id"], "--role", "agent",
            "--verdict", "accept", "--comment", "Complete null search audited before contradiction discovery.")
        original = evaluation.report(baseline)
        pair = next(case for case in original["random"]["answers"][0]["checks"]["relationship"]
                    if case["evidence"].get("teacher_numbers") == ["2"]
                    and case["evidence"].get("heading_number") == "2")
        source = next(group["experiment"] for group in original["experiments"]
                      if any(case["id"] == pair["id"] for case in group["cases"]))
        verification = self.root / "null-contradiction-verification"
        fixture.native("prepare", verification, "--from", source, "--only", pair["id"], "--reasoning-effort", "high")
        fixture.native("run", verification, "--max-new-attempts", 2)
        fixture.native("review", verification, "--case", pair["id"], "--role", "agent",
            "--verdict", "accept", "--comment", "Exact positive comparison independently audited.")
        result = coverage.collect(output, self.root / "null-contradiction-collected.json",
            verification_experiments=[verification])
        answer = result["random"]["answers"][0]
        self.assertEqual(answer["scoring"]["status"], "pending")
        self.assertNotIn("coverage", answer["scoring"].get("scores", {}))
        self.assertTrue(answer["coverage_inconsistencies"])
        self.assertTrue(any(premise["case_id"] == pair["id"] for premise in answer["premises"]))


if __name__ == "__main__":
    unittest.main()
