"""Offline preflight through native preparation, execution and attributed review."""
import json
import tempfile
import unittest
from pathlib import Path

from sse_multivector import test_distillation_review_evaluation as fixtures


class DistillationReviewPreflightTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.fixture = fixtures.DistillationReviewEvaluationTests()
        self.fixture.root = self.root

    def prepare(self, name="fixture", reason="Fixture semantic verdict.", supported=True, run_relationships=True):
        from sse_multivector import distillation_review_assessment as assessment
        from sse_multivector import distillation_review_evaluation as evaluation
        teacher = fixtures.subjects(("1", "Fruits"), ("2", "Cable A"))
        student = fixtures.subjects(("1", "Fruits"), ("1.1", "Novel subject"), ("2", "Novel subject"))
        selection = self.fixture.selection([dict(note_id="validation-a", post="Fruit and a cable.",
            teacher=teacher, answer=fixtures.answer(student))], name=name)
        assessments = self.root / (name + "-assessments")
        assessment.record(selection, "R01", assessments, teacher_meanings=[
            dict(teacher_numbers=["1"], required=True), dict(teacher_numbers=["2"], required=False)],
            reason="Frozen fixture teacher groups.")
        worker = self.fixture.worker()
        worker.write_text(worker.read_text().replace('"teacher_id": None', '"teacher_id": "T01"')
                          .replace("Fixture semantic verdict.", reason))
        if not supported:
            worker.write_text(worker.read_text().replace('else {"valid": True,',
                'else {"valid": not prompt.startswith("DSSv2"),'))
        worker = worker.rename(self.root / (name + "-worker"))
        directory = self.root / (name + "-evaluation")
        prepared = evaluation.prepare(selection, directory, runner_binary=worker, assessment_directory=assessments)
        for group in prepared["experiments"]:
            if not run_relationships and group["check"] == "relationship":
                continue
            self.fixture.native("run", group["path"], "--max-new-attempts", "30")
        return directory

    def test_native_preflight_groups_current_required_versions_without_inference(self):
        directory = self.prepare()
        calls = (self.root / "calls.json").read_bytes()
        value = json.loads(self.fixture.native("show-distillation-review-evaluation", directory, "--unreviewed"))
        self.assertGreater(value["summary"]["unreviewed_versions"], 0)
        self.assertTrue(any(len(row["aliases"]) > 1 for row in value["unreviewed"]))
        self.assertTrue(all(row["origin"] != "mechanical" for row in value["unreviewed"]))
        relationships = [row for row in value["unreviewed"] if row["check"] == "relationship"]
        self.assertTrue(relationships)
        self.assertTrue(all(alias["evidence"].get("teacher_numbers") != ["2"]
                            for row in relationships for alias in row["aliases"]))
        self.assertEqual((self.root / "calls.json").read_bytes(), calls)

    def preflight(self, directory, *args):
        return json.loads(self.fixture.native("show-distillation-review-evaluation", directory, "--unreviewed", *args))

    def test_exact_alias_proofs_reuse_but_new_raw_output_and_stale_reviews_need_audit(self):
        first = self.prepare()
        value = self.preflight(first)
        source = next(row for row in value["unreviewed"] if row["check"] == "support" and len(row["aliases"]) > 1)
        alias = source["aliases"][0]
        self.fixture.native("review", alias["experiment"], "--case", alias["case_id"], "--role", "agent",
                            "--verdict", "uncertain", "--comment", "Exact version has been assessed, not accepted.")
        reused = self.preflight(first)
        known = next(row for row in reused["reusable_reviews"] if row["inputs"] == source["inputs"])
        self.assertEqual(known["output"], source["output"])
        self.assertEqual(known["assessments"][0]["review"]["verdict"], "uncertain")
        second = self.prepare("changed", reason="Changed complete explanation.")
        pending = self.preflight(second)
        changed = next(row for row in pending["unreviewed"] if row["check"] == "support" and row["inputs"] == source["inputs"])
        self.assertNotEqual(changed["output"], source["output"])
        target = changed["aliases"][0]
        self.fixture.native("review", target["experiment"], "--from-experiment", alias["experiment"])
        self.assertTrue(any(row["inputs"] == source["inputs"] and row["check"] == "support"
                            for row in self.preflight(second)["unreviewed"]))
        # Stale attribution is a real saved review whose previous output digest no longer applies.
        from experiment_runner import extraction_pipeline as engine
        from experiment_runner import inputs
        engine._append_json_line(Path(target["experiment"]) / "reviews.jsonl", dict(
            case_id=target["case_id"], role="agent", verdict="accept", comment="Historical exact output assessment.",
            input_sha256=changed["input_sha256"], output_sha256=inputs.digest(source["output"])))
        self.assertTrue(any(row["inputs"] == source["inputs"] and row["check"] == "support"
                            for row in self.preflight(second)["unreviewed"]))

    def test_external_exact_assessments_recognize_reject_without_accepting_it(self):
        import hashlib
        directory = self.prepare()
        value = self.preflight(directory)
        row = value["unreviewed"][0]
        audit = self.root / "existing-audit.jsonl"
        audit.write_text(json.dumps(dict(check=row["check"], input_sha256=row["input_sha256"],
            output_sha256=hashlib.sha256(row["output"].encode()).hexdigest(), verdict="reject",
            reason="Existing exact complete output was found incorrect.")) + "\n")
        recognized = self.preflight(directory, "--premise-audit", audit)
        self.assertEqual(recognized["summary"]["unreviewed_versions"], value["summary"]["unreviewed_versions"] - 1)
        from sse_multivector import distillation_coverage_search as coverage
        from experiment_runner import experiment
        native = experiment.report(Path(row["aliases"][0]["experiment"]), include_request_preview=False)
        case = next(case for case in native["cases"] if case["id"] == row["aliases"][0]["case_id"])
        audits = coverage._premise_audits([dict(path=str(audit), sha256=hashlib.sha256(audit.read_bytes()).hexdigest())],
                                         directory, {})
        self.assertIsNone(coverage._accepted_premise(case, audits))

    def test_unsupported_child_does_not_require_actual_edge_with_same_subject_case_id(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        for run_relationships in (True, False):
            with self.subTest(run_relationships=run_relationships):
                directory = self.prepare(str(run_relationships), supported=False,
                                         run_relationships=run_relationships)
                report = evaluation.report(directory, include_request_summary=False)
                actual = {(native["experiment"], row["id"]) for native in report["experiments"]
                          for row in native["cases"] if row["evidence"].get("role") == "actual_relationship"
                          and row.get("origin") != "mechanical"}
                self.assertTrue(actual)
                value = self.preflight(directory)
                selected = {(alias["experiment"], alias["case_id"]) for row in value["unreviewed"]
                            for alias in row["aliases"]}
                selected.update((row["experiment"], row["case_id"]) for row in value["pending"])
                self.assertFalse(actual & selected)


if __name__ == "__main__":
    unittest.main()
