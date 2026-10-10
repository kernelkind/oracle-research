"""Offline reviewer effort analysis through the production command and receipts."""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from sse_multivector import distillation_review_effort_analysis as analysis
from sse_multivector.distillation_review_effort_analysis import (
    analyze, compare_verdicts, freeze_panel, normalize, reference_agreement,
)

PROJECT = Path(__file__).resolve().parents[1]
MODULE = "sse_multivector.distillation_review_effort_analysis"


class DistillationReviewEffortAnalysisCliTests(unittest.TestCase):
    def test_missing_panel_is_rejected_before_loading_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "must-not-exist.json"
            result = subprocess.run([sys.executable, "-m", MODULE,
                "--compact", str(root / "missing-report.json"), "--effort", "xhigh",
                "--output", str(output)], cwd=PROJECT, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("following arguments are required: --panel", result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            self.assertFalse(output.exists())

    def test_native_fake_receipts_compact_freeze_and_compare_without_dispatch(self):
        from sse_multivector import distillation_review_assessment as assessment
        from sse_multivector import distillation_review_evaluation as evaluation
        from sse_multivector import test_distillation_review_evaluation as fixtures
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fixture = fixtures.DistillationReviewEvaluationTests()
            fixture.root = root
            teacher = fixtures.subjects(("1", "Cable A"))
            student = fixtures.subjects(("1", "Different wording"), ("2", "Different wording"), ("3", "Cable A"))
            selected = fixture.selection([dict(note_id=f"validation-{i}", post="Cable A.",
                teacher=teacher, answer=fixtures.answer(student)) for i in range(5)], random_count=5)
            bundle = analysis.read(selected)
            answers = bundle["random"]["answers"]
            directory = root / "assessments"
            for answer in answers:
                assessment.record(selected, answer["id"], directory,
                    teacher_meanings=[dict(teacher_numbers=["1"], required=True)],
                    reason="Independent synthetic fixture teacher context.")
            for answer in answers:
                assessment.record(selected, answer["id"], directory,
                    expectations=dict(
                        matching=[dict(student_number=number, teacher_number="1" if number == "3" else None,
                                       reason="Exact fixture wording or unmatched wording.") for number in ("1", "2", "3")],
                        support=[dict(student_number=number, valid=number == "3", reason="Fixture post names only Cable A.")
                                 for number in ("1", "2", "3")], relationships=[],
                        compatibility=[dict(teacher_numbers=["1"], compatible_heading_numbers=["3"],
                                            reason="Only the exact heading preserves the teacher meaning.")]),
                    reason="Independent synthetic fixture assessment.")
            assessment.freeze(selected, directory)
            worker = fixture.worker()
            reports = {}
            for effort in ("xhigh", "high"):
                output = root / effort
                prepared = evaluation.prepare(selected, output, runner_binary=worker,
                    assessment_directory=directory, history_root=root, reasoning_effort=effort)
                # The existing native CLI invokes only the local fake worker.
                for entry in prepared["experiments"]:
                    fixture.native("run", entry["path"])
                reports[effort] = evaluation.report(output)
            call_log = (root / "calls.json").read_bytes()
            self.assertEqual(len(json.loads(call_log)), 6)
            labels = {answer["id"]: f"R{i:02}" for i, answer in enumerate(answers, 1)}
            note_ids = {answer["id"]: answer["note_id"] for answer in answers}
            cases = {}
            for native in reports["xhigh"]["experiments"]:
                for case in native["cases"]:
                    if case.get("origin") == "mechanical":
                        continue
                    evidence = case["evidence"]
                    check = evidence["check"]
                    sha = hashlib.sha256(case["prompt"].encode()).hexdigest()
                    row = cases.setdefault(check + ":" + sha, dict(key=check + ":" + sha, check=check,
                        prompt_sha256=sha, input_sha256=case["input_sha256"], all_input_sha256=[], aliases=[]))
                    row["all_input_sha256"].append(case["input_sha256"])
                    row["aliases"].append(dict(alias=labels[evidence["answer_id"]], answer_id=evidence["answer_id"],
                        case_id=case["id"], cohort=evidence["cohort"], note_id=note_ids[evidence["answer_id"]],
                        role=evidence.get("role", check), input_sha256=case["input_sha256"],
                        reference_status=evidence["expectation_status"],
                        reference_label=evidence["expected_teacher_id" if check == "matching" else "expected_valid"]))
            sources = {str(path): analysis.file_hash(path) for path in
                       (selected, selected.parent / "selection.complete.json", directory / "assessment.complete.json")}
            panel = root / "panel.json"
            analysis.write(panel, dict(sources=sources,
                assessment_sources=assessment.load_assessments(directory, bundle)["sources"],
                settings=dict(baseline=bundle["settings"]), cases=list(cases.values()),
                stages=[dict(size=5, aliases=list(labels.values()), answer_ids=list(labels), case_keys=list(cases))]))
            paths = {}
            for effort, report in reports.items():
                source = root / (effort + ".json.gz")
                analysis.write(source, report)
                paths[effort] = root / (effort + ".compact.json.gz")
                args = [sys.executable, "-m", MODULE, "--panel", str(panel), "--compact", str(source),
                        "--effort", effort, "--output", str(paths[effort])]
                if effort == "xhigh":
                    args.append("--freeze-baseline")
                result = subprocess.run(args, cwd=PROJECT, capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr)
            frozen = analysis.read(paths["xhigh"])
            self.assertEqual(len(frozen["frozen_panel_verdicts"]), 3)
            self.assertTrue(all(row["chosen"]["receipt"] for row in frozen["frozen_panel_verdicts"].values()))
            result_path = root / "paired.json.gz"
            result = subprocess.run([sys.executable, "-m", MODULE, "--panel", str(panel), "--stage", "5",
                "--report", "xhigh=" + str(paths["xhigh"]), "--report", "high=" + str(paths["high"]),
                "--output", str(result_path)], cwd=PROJECT, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            paired = analysis.read(result_path)
            self.assertEqual(paired["summary"]["distinct_prompts"], 3)
            self.assertEqual(paired["summary"]["paired"]["high"], {"agree": 3})
            self.assertEqual(paired["summary"]["raw_agent_reference"]["high"],
                             {"agrees_reference": 1, "disagrees_reference": 2})
            self.assertFalse(paired["summary"]["qualification_blocked"])
            self.assertEqual(paired["missing_native_pool_cases"], [])
            self.assertEqual({alias["note_id"] for row in paired["rows"] for alias in row["aliases"]}, set(note_ids.values()))
            self.assertEqual((root / "calls.json").read_bytes(), call_log)


class DistillationReviewEffortAnalysisTests(unittest.TestCase):
    def test_same_verdict_cancels(self):
        self.assertEqual(compare_verdicts(False, False), "agree")
        self.assertEqual(reference_agreement([dict(reference_status="agent_assessed", reference_label=True)],
            dict(status="valid", raw_verdicts=[False]))["status"], "disagrees_reference")

    def test_teacher_group_equivalence(self):
        mapping = {"T01": ["1", "2"], "T02": ["1", "2"]}
        self.assertEqual(compare_verdicts(normalize("matching", "T01", mapping),
                                         normalize("matching", "T02", mapping)), "agree")

    def test_missing_baseline_cannot_be_frozen(self):
        case = dict(key="support:h", check="support", prompt_sha256="h", aliases=[dict(answer_id="A")])
        with self.assertRaisesRegex(ValueError, "missing prompts"):
            freeze_panel(dict(cases=[case]), dict(rows=[]), {"A": {}})

    def test_baseline_choice_is_order_independent_and_conflicts_stay_visible(self):
        case = dict(key="support:h", check="support", prompt_sha256="h", aliases=[dict(answer_id="A")])
        rows = [dict(id=identifier, experiment="native", check="support", prompt_sha256="h", status="valid",
            parsed=dict(valid=value), receipt=dict(record_sha256=identifier), original_receipt={}, reused=False)
            for identifier, value in (("b", True), ("a", False))]
        left = freeze_panel(dict(cases=[case]), dict(rows=rows), {"A": {}})
        right = freeze_panel(dict(cases=[case]), dict(rows=list(reversed(rows))), {"A": {}})
        self.assertEqual(left, right)
        self.assertEqual(left, json.loads(json.dumps(left)))
        self.assertEqual(left[case["key"]]["chosen"]["case_id"], "a")
        self.assertEqual(left[case["key"]]["status"], "conflicting_verdicts")

    def test_missing_rows_and_role_overlap_count_once(self):
        aliases = [dict(alias="R01", answer_id="A", case_id="edge", note_id="note-A", cohort="random",
                        role=role, reference_status="agent_assessed", reference_label=True)
                   for role in ("actual_relationship", "compatibility")]
        case = dict(key="relationship:h", check="relationship", prompt_sha256="h", input_sha256="i", aliases=aliases)
        panel = dict(stages=[dict(size=1, aliases=["R01"], case_keys=[case["key"]])], cases=[case])
        pending = dict(id="edge", experiment="native", check="relationship", prompt_sha256="h", status="skipped")
        result = analyze(panel, 1, {"xhigh": dict(rows=[pending]), "high": dict(rows=[pending])}, {"A": {}})
        self.assertEqual(result["summary"]["distinct_prompts"], 1)
        self.assertEqual(result["summary"]["paired"]["high"], {"missing": 1})
        self.assertEqual(len(result["missing_native_pool_cases"]), 2)
        self.assertEqual(result["summary"]["roles"]["compatibility"]["distinct_prompts"], 1)
        self.assertEqual({alias["note_id"] for alias in result["rows"][0]["aliases"]}, {"note-A"})
        aliases[1].update(reference_status="unresolved", reference_label=None)
        valid = dict(pending, status="valid", parsed=dict(valid=True), receipt=dict(record_sha256="r"),
                     original_receipt={}, reused=False)
        result = analyze(panel, 1, {"xhigh": dict(rows=[valid]), "high": dict(rows=[valid])}, {"A": {}})
        self.assertEqual(result["summary"]["paired"]["high"], {"agree": 1})
        self.assertEqual(result["summary"]["roles"]["compatibility"]["raw_agent_reference"]["high"],
                         {"unresolved_reference": 1})
