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
    def inventory_fixture(self, *, two_notes=False):
        from sse_multivector import distillation_review_assessment as assessment
        fixture = fixtures.DistillationReviewPreviewTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        teacher = fixtures.subjects(("1", "Cables"))
        notes = [dict(note_id="validation-a", post="Cables are here.", teacher=teacher,
                      answer=fixtures.answer(teacher))]
        if two_notes:
            notes.append(dict(note_id="validation-b", post="Tools are here.",
                teacher=fixtures.subjects(("1", "Tools")),
                answer=fixtures.answer(fixtures.subjects(("1", "Tools")))))
        manifest, outputs = fixture.fixture(notes)
        original = trial.prepare_trial(manifest, outputs, fixture.root / "original", random_count=1, hard_count=0)
        original_path = Path(original["selection_path"])
        source = fixture.root / "assessments"
        groups = [dict(teacher_numbers=["1"], required=True)]
        assessment.record(original_path, "R01", source, teacher_meanings=groups, reason="Explicit fixture policy.")
        labels = dict(matching=[dict(student_number="1", teacher_number="1", reason="Exact wording.")],
            support=[dict(student_number="1", valid=True, reason="Trusted wording.")], relationships=[],
            compatibility=[dict(teacher_numbers=["1"], compatible_heading_numbers=["1"], reason="Equality.")])
        assessment.record(original_path, "R01", source, expectations=labels, reason="Original answer judgments.")
        assessment.freeze(original_path, source)
        expanded = trial.prepare_trial(manifest, outputs, fixture.root / "expanded",
            random_count=len(notes) * 2, hard_count=0, seed="inventory-expanded")
        return fixture, source, Path(expanded["selection_path"]), groups

    def test_inventory_reuses_bound_teacher_context_without_answer_expectations(self):
        from sse_multivector import distillation_review_assessment as assessment
        from sse_multivector import distillation_run as run
        fixture, source, selection, groups = self.inventory_fixture()
        teacher_path = next(source.glob("teacher-*.json"))
        frozen = teacher_path.read_bytes()
        output = fixture.root / "inventory"
        report = assessment.prepare_inventory(selection, output, [source])
        self.assertEqual(report["inference_calls"], 0)
        self.assertEqual(report["context_count"], 1)
        self.assertEqual(report["missing_contexts"], [])
        loaded = assessment.load_assessments(output, trial.load_trial(selection))
        self.assertEqual(len(loaded["contexts"]), 2)
        self.assertTrue(all(value == groups for value in loaded["contexts"].values()))
        self.assertEqual(loaded["expectations"], {})
        self.assertEqual(loaded["sources"][str(teacher_path)], run.sha256(teacher_path))
        self.assertEqual(teacher_path.read_bytes(), frozen)
        with self.assertRaisesRegex(ValueError, "exists|frozen"):
            assessment.prepare_inventory(selection, output, [source])
        with self.assertRaisesRegex(ValueError, "frozen"):
            assessment.record_exact_groups(selection, "R01", output, ["1"], [],
                                           reason="A frozen inventory cannot acquire additional records.")

    def test_incomplete_inventory_lists_missing_contexts_without_defaulting_policy(self):
        from sse_multivector import distillation_review_assessment as assessment
        fixture, source, selection, _ = self.inventory_fixture(two_notes=True)
        output = fixture.root / "partial-inventory"
        report = assessment.prepare_inventory(selection, output, [source])
        self.assertEqual(len(report["missing_contexts"]), 1)
        loaded = assessment.load_assessments(output, trial.load_trial(selection))
        self.assertEqual(len(loaded["contexts"]), 2)
        self.assertEqual(loaded["expectations"], {})
        missing = report["missing_contexts"][0]
        self.assertEqual(len(missing["answer_ids"]), 2)
        additional = fixture.root / "additional-assessments"
        assessment.record_exact_groups(selection, missing["answer_ids"][0], additional, [], ["1"],
                                       reason="Explicit optional fixture policy for the missing context.")
        complete = fixture.root / "complete-inventory"
        completed = assessment.prepare_inventory(selection, complete, [source, additional])
        self.assertEqual(completed["missing_contexts"], [])
        contexts = assessment.load_assessments(complete, trial.load_trial(selection))["contexts"]
        self.assertEqual(len(contexts), 4)
        self.assertFalse(contexts[missing["answer_ids"][0]][0]["required"])
        self.assertEqual(len(assessment.load_assessments(output, trial.load_trial(selection))["contexts"]), 2)

    def test_inventory_verifies_original_context_and_selection_provenance(self):
        from sse_multivector import distillation_review_assessment as assessment
        from sse_multivector import distillation_run as run
        fixture, source, selection, _ = self.inventory_fixture()
        output = fixture.root / "inventory"
        assessment.prepare_inventory(selection, output, [source])
        teacher_path = next(source.glob("teacher-*.json"))
        data = run.read_json(teacher_path)
        data["teacher_meanings"][0]["required"] = False
        run.write_json(teacher_path, data)
        with self.assertRaisesRegex(ValueError, "hash|source"):
            assessment.load_assessments(output, trial.load_trial(selection))

    def test_inventory_rejects_unbound_context_and_conflicting_policy(self):
        from sse_multivector import distillation_review_assessment as assessment
        from sse_multivector import distillation_run as run
        fixture, source, selection, _ = self.inventory_fixture(two_notes=True)
        selected = trial.load_trial(selection)
        original = run.read_json(next(source.glob("teacher-*.json")))
        represented = next(row for _, row in assessment.answers(selected)
                           if assessment._context_key(row) == original["context_key"])
        conflicting = fixture.root / "conflicting"
        assessment.record_exact_groups(selection, represented["id"], conflicting, [], ["1"],
                                       reason="Conflicting explicit optional policy.")
        with self.assertRaisesRegex(ValueError, "conflicting"):
            assessment.prepare_inventory(selection, fixture.root / "conflict-inventory", [source, conflicting])
        missing = next(row for _, row in assessment.answers(selected)
                       if assessment._context_key(row) != original["context_key"])
        unbound = fixture.root / "unbound"
        path = unbound / ("teacher-" + assessment._context_key(missing) + ".json")
        original["context_key"] = assessment._context_key(missing)
        run.write_json(path, original)
        with self.assertRaisesRegex(ValueError, "original selection"):
            assessment.prepare_inventory(selection, fixture.root / "unbound-inventory", [unbound])

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

    def test_legacy_frozen_path_labels_load_unchanged_but_new_labels_are_rejected(self):
        from sse_multivector import distillation_review_assessment as assessment
        from sse_multivector import distillation_run as run
        fixture = fixtures.DistillationReviewPreviewTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        teacher = fixtures.subjects(("1", "Cables"), ("1.1", "Cable A"), ("1.1.1", "2 m cable A"))
        student = fixtures.subjects(("1", "Cables"), ("1.1", "2 m cable A"))
        manifest, outputs = fixture.fixture([dict(note_id="validation-a", post="Cable A is 2 m long.",
            teacher=teacher, answer=fixtures.answer(student))])
        selected = trial.prepare_trial(manifest, outputs, fixture.root / "trial", random_count=1, hard_count=0)
        selection = Path(selected["selection_path"])
        bundle = trial.load_trial(selection)
        answer_id = bundle["random"]["answers"][0]["id"]
        groups = [dict(teacher_numbers=[number], required=number == "1.1.1") for number in ("1", "1.1", "1.1.1")]
        correct = dict(
            matching=[dict(student_number=number, teacher_number=teacher_number, reason="Exact fixture wording.")
                for number, teacher_number in (("1", "1"), ("1.1", "1.1.1"))],
            support=[dict(student_number=number, valid=True, reason="Trusted source wording.") for number in ("1", "1.1")],
            relationships=[dict(child="1.1", valid=True, reason="Trusted ancestor path.")],
            compatibility=[dict(teacher_numbers=["1.1.1"], compatible_heading_numbers=["1", "1.1"],
                                reason="Trusted path and equality.")])
        for field, wrong_rows, message in (
            ("compatibility", [dict(teacher_numbers=["1.1.1"], compatible_heading_numbers=["1.1"],
                reason="Legacy false ancestor compatibility judgment.")], "trusted compatibility"),
            ("relationships", [dict(child="1.1", valid=False, reason="Legacy false ancestor relationship judgment.")],
                "trusted relationship")):
            with self.subTest(field=field):
                directory = fixture.root / (field + "-legacy")
                assessment.record(selection, "R01", directory, teacher_meanings=groups, reason="Independent fixture context.")
                saved = assessment.record(selection, "R01", directory, expectations=correct, reason="Complete fixture judgments.")
                assessment.freeze(selection, directory)
                answer_path = Path(saved["path"])
                data = run.read_json(answer_path)
                self.assertEqual(data["schema_version"], 2)
                data["schema_version"] = 1
                data["expectations"][field] = wrong_rows
                run.write_json(answer_path, data)
                seal_path = directory / "assessment.complete.json"
                seal = run.read_json(seal_path)
                seal[str(answer_path)] = run.sha256(answer_path)
                run.write_json(seal_path, seal)
                frozen = {path: path.read_bytes() for path in (answer_path, seal_path, selection)}
                loaded = assessment.load_assessments(directory, bundle)
                self.assertEqual(loaded["expectations"][answer_id], data["expectations"])
                self.assertEqual({path: path.read_bytes() for path in frozen}, frozen)
                current = fixture.root / (field + "-current")
                assessment.record(selection, "R01", current, teacher_meanings=groups, reason="Independent fixture context.")
                with self.assertRaisesRegex(ValueError, message):
                    assessment.record(selection, "R01", current, expectations=dict(correct, **{field: wrong_rows}),
                                      reason="New contradictory path judgment must be rejected.")
                data["schema_version"] = 2
                run.write_json(answer_path, data)
                with self.assertRaisesRegex(ValueError, message):
                    assessment.load_assessments(directory, bundle)
                for version in (True, 0, 3):
                    data["schema_version"] = version
                    run.write_json(answer_path, data)
                    with self.assertRaisesRegex(ValueError, "answer assessment reference"):
                        assessment.load_assessments(directory, bundle)


if __name__ == "__main__":
    unittest.main()
