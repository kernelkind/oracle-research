"""Pre-call reference judgments through the native review workflow."""
import json
from pathlib import Path
import subprocess
import sys
import unittest

from sse_multivector import test_distillation_review_preview as fixtures
from sse_multivector import distillation_review_trial as trial


PROJECT = Path(__file__).resolve().parents[1]
LAUNCHER = PROJECT.parent / "experiment-runner/bin/experiment-runner"


class DistillationReviewAssessmentTests(unittest.TestCase):
    def test_native_cli_exposes_source_bound_assessment(self):
        result = subprocess.run([sys.executable, str(LAUNCHER), "--project-root", str(PROJECT),
            "assess-distillation-review", "--help"], cwd=PROJECT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--teacher-meanings", result.stdout)
        self.assertIn("--expectations", result.stdout)
        self.assertIn("--required-numbers", result.stdout)
        self.assertIn("--wording-expectations", result.stdout)

    def test_teacher_inspection_hides_candidate_and_teacher_context_is_frozen(self):
        from sse_multivector import distillation_review_assessment as assessment
        fixture = fixtures.DistillationReviewPreviewTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        manifest, outputs = fixture.fixture()
        selection = trial.prepare_trial(manifest, outputs, fixture.root / "trial", random_count=1, hard_count=0)
        path = Path(selection["selection_path"])
        visible = assessment.inspect(path, "R01", teacher_only=True)
        self.assertNotIn("student", visible)
        self.assertNotIn("model", visible)
        self.assertNotIn("version", visible)
        self.assertNotIn("raw_answer", visible)
        groups = [{"teacher_numbers": ["1"], "required": False},
            {"teacher_numbers": ["1.1", "1.2"], "required": True},
            {"teacher_numbers": ["1.3"], "required": True},
            {"teacher_numbers": ["2"], "required": False},
            {"teacher_numbers": ["2.1"], "required": True}]
        directory = fixture.root / "assessment"
        assessment.record(path, "R01", directory, teacher_meanings=groups, reason="Trusted teacher source distinctions.")
        loaded = assessment.load_assessments(directory, trial.load_trial(path))
        answer_id = selection["random"]["answers"][0]["id"]
        self.assertEqual(loaded["contexts"][answer_id], groups)
        with self.assertRaisesRegex(ValueError, "frozen|exists"):
            assessment.record(path, "R01", directory, teacher_meanings=groups,
                              reason="A later attempt must not overwrite the frozen reference.")

    def test_record_rejects_gold_that_contradicts_mechanical_matching(self):
        from sse_multivector import distillation_review_assessment as assessment
        fixture = fixtures.DistillationReviewPreviewTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        manifest, outputs = fixture.fixture()
        selection = trial.prepare_trial(manifest, outputs, fixture.root / "trial", random_count=1, hard_count=0)
        path = Path(selection["selection_path"])
        row = selection["random"]["answers"][0]
        from sse_multivector import distillation_review as review
        index = review._TeacherIndex(row["teacher"])
        groups = [{"teacher_numbers": numbers, "required": False} for numbers in index.numbers.values()]
        directory = fixture.root / "assessment"
        assessment.record(path, "R01", directory, teacher_meanings=groups, reason="Test context.")
        matched = next(s for s in row["student"] if s["subject"] in index.by_subject)
        wrong = next(s["number"] for s in row["teacher"] if s["subject"] != matched["subject"])
        labels = dict(matching=[dict(student_number=matched["number"], teacher_number=wrong, reason="Wrong label.")],
                      support=[], relationships=[], compatibility=[])
        with self.assertRaisesRegex(ValueError, "contradicts exact"):
            assessment.record(path, "R01", directory, expectations=labels, reason="Contradiction rejected.")

    def test_wording_judgments_cover_duplicates_and_frozen_selection_binding(self):
        from sse_multivector import distillation_review_assessment as assessment
        from sse_multivector import distillation_review as review
        fixture = fixtures.DistillationReviewPreviewTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        manifest, outputs = fixture.fixture()
        selected = trial.prepare_trial(manifest, outputs, fixture.root / "trial", random_count=1, hard_count=0)
        path = Path(selected["selection_path"])
        row = selected["random"]["answers"][0]
        directory = fixture.root / "assessment"
        index = review._TeacherIndex(row["teacher"])
        assessment.record_exact_groups(path, "R01", directory, [],
            [numbers[0] for numbers in index.numbers.values()], reason="Explicit broad fixture meanings.")
        words, pairs = {}, {}
        students = {s["number"]: s["subject"] for s in row["student"]}
        for number, subject in students.items():
            words.setdefault(subject, number)
            if "." in number:
                pairs.setdefault((students[number.rpartition(".")[0]], subject), number)
        value = dict(matching=[dict(student_number=n, teacher_number=next(iter(index.numbers[index.by_subject[s]]), None)
            if s in index.by_subject else None, reason="Explicit fixture match.") for s, n in words.items()],
            support=[dict(student_number=n, valid=True, reason="Explicit fixture support.") for n in words.values()],
            relationships=[dict(child=n, valid=True, reason="Explicit fixture edge.") for n in pairs.values()],
            compatibility=[])
        incomplete = dict(value, support=value["support"][:-1])
        with self.assertRaisesRegex(ValueError, "omitted distinct"):
            assessment.record_wording_expectations(path, "R01", directory, incomplete, reason="Incomplete input rejected.")
        assessment.record_wording_expectations(path, "R01", directory, value, reason="All distinct inputs assessed.")
        loaded = assessment.load_assessments(directory, trial.load_trial(path))
        labels = loaded["expectations"][row["id"]]
        self.assertEqual(len(labels["matching"]), len(students))
        self.assertEqual(len(labels["support"]), len(students))
        self.assertEqual(len(labels["relationships"]), sum("." in n for n in students))
        different = trial.prepare_trial(manifest, outputs, fixture.root / "different", random_count=1, hard_count=0,
                                       seed="different-selection-binding")
        with self.assertRaisesRegex(ValueError, "assessment selection differs"):
            assessment.load_assessments(directory, trial.load_trial(different["selection_path"]))
        assessment.freeze(path, directory)
        with self.assertRaisesRegex(ValueError, "frozen"):
            assessment.record_wording_expectations(path, "R01", directory, value, reason="Frozen input rejected.")


if __name__ == "__main__":
    unittest.main()
