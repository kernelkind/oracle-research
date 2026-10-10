"""Frozen offline final-trial sampling through production validation paths."""
import json
from pathlib import Path
import tempfile
import unittest

from sse_multivector import distillation_run as run
from sse_multivector import test_distillation_review_preview as fixtures

TEACHER, answer = fixtures.TEACHER, fixtures.answer


class DistillationReviewTrialTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def fixture(self, notes):
        fixture = fixtures.DistillationReviewPreviewTests("runTest")
        fixture.root = self.root
        return fixture.fixture(notes, models=3)

    def test_random_sample_preserves_complete_invalid_answer(self):
        from sse_multivector.distillation_review_trial import prepare_trial
        raw = "not a JSON answer"
        manifest, models = self.fixture([dict(note_id="validation-invalid",
            post="Cable A is 2 m long.", teacher=TEACHER, answer=answer([], raw=raw))])
        report = prepare_trial(manifest, models, self.root / "trial",
                               random_count=1, hard_count=0, seed="invalid-fixture")
        selected = report["random"]["answers"]
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0]["raw_answer"]["raw"], raw)
        self.assertTrue(selected[0]["errors"])
        self.assertEqual(selected[0]["student"], [])
        self.assertEqual(report["random"]["totals"]["invalid_outputs"], 1)
        self.assertEqual(report["random"]["totals"]["checks"]["matching"]["occurrences"], 0)
        frozen = json.loads(Path(report["selection_path"]).read_text())
        self.assertEqual(frozen["random"]["answers"], selected)

    def notes(self, count):
        return [dict(note_id=f"validation-{i}", post=f"Cable A is 2 m long. Note {i}.",
                     teacher=TEACHER, answer=answer(fixtures.STUDENT)) for i in range(count)]

    def test_seeded_balanced_random_and_disjoint_diverse_challenge(self):
        from sse_multivector.distillation_review_trial import prepare_trial, load_trial
        notes = self.notes(8)
        notes[0]["note_id"] = "a88fff1a7b5647c650a9328fb3ab2f4ab7a4b7e9cf2db210caf42e8c19b49cb5"
        manifest, models = self.fixture(notes)
        report = prepare_trial(manifest, models, self.root / "trial", random_count=8, hard_count=4)
        repeated = prepare_trial(manifest, models, self.root / "repeat", random_count=8, hard_count=4)
        random_rows, hard_rows = report["random"]["answers"], report["challenge"]["answers"]
        self.assertEqual(random_rows, repeated["random"]["answers"])
        self.assertEqual(hard_rows, repeated["challenge"]["answers"])
        quotas = list(report["selection_policy"]["version_quotas"].values())
        self.assertLessEqual(max(quotas) - min(quotas), 1)
        self.assertEqual(sum(quotas), 8)
        self.assertEqual(report["random"]["distinct_notes"], 8)
        self.assertEqual(report["random"]["previously_used_note_answers"], 1)
        self.assertFalse(random_rows[0]["previously_used_note"])
        self.assertEqual(report["challenge"]["distinct_notes"], 4)
        self.assertEqual(len({a["selection_pattern"] for a in hard_rows}), 4)
        self.assertFalse({a["id"] for a in random_rows} & {a["id"] for a in hard_rows})
        for selected in random_rows + hard_rows:
            self.assertEqual(selected["student"], fixtures.STUDENT)
            self.assertEqual(selected["teacher"], TEACHER)
        self.assertEqual(report["random"]["totals"]["subject_occurrences"], 8 * len(fixtures.STUDENT))
        self.assertEqual(load_trial(report["selection_path"])["random"], report["random"])

    def test_random_keeps_valid_empty_and_invalid_outputs_without_checks(self):
        from sse_multivector.distillation_review_trial import prepare_trial, load_trial
        notes = self.notes(2)
        notes[0]["answer"] = answer([])
        notes[1]["answer"] = answer([], raw="{", truncated=True)
        manifest, models = self.fixture(notes)
        report = prepare_trial(manifest, models, self.root / "trial", random_count=12, hard_count=0)
        totals = report["random"]["totals"]
        self.assertEqual((totals["valid_outputs"], totals["invalid_outputs"], totals["empty_outputs"]), (6, 6, 6))
        self.assertEqual(totals["subject_occurrences"], 0)
        self.assertEqual(load_trial(report["selection_path"])["random"]["totals"], totals)

    def test_loader_rejects_changed_source_and_changed_selected_evidence(self):
        from sse_multivector.distillation_review_trial import prepare_trial, load_trial
        manifest, models = self.fixture(self.notes(2))
        report = prepare_trial(manifest, models, self.root / "trial", random_count=2, hard_count=0)
        path = Path(report["selection_path"])
        saved = run.read_json(path)
        saved["random"]["answers"][0]["post"] = "Changed post."
        run.write_json(path, saved)
        with self.assertRaisesRegex(ValueError, "selection hash"):
            load_trial(path)
        run.write_json(path.parent / "selection.complete.json", {path.name: run.sha256(path)})
        with self.assertRaisesRegex(ValueError, "evidence differs"):
            load_trial(path)
        run.write_json(path, {k: v for k, v in report.items() if k != "selection_path"})
        run.write_json(path.parent / "selection.complete.json", {path.name: run.sha256(path)})
        generation = Path(report["random"]["answers"][0]["generation"]["path"])
        generation.write_text(generation.read_text() + "\n")
        with self.assertRaisesRegex(ValueError, "source hash"):
            load_trial(path)

    def test_bad_unselected_stage_aborts_before_publishing_selection(self):
        from sse_multivector.distillation_review_trial import prepare_trial
        manifest, models = self.fixture(self.notes(2))
        (models[-1] / "evaluations/checkpoint-1/subjects-0000.json").write_text("corrupt")
        output = self.root / "trial"
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            prepare_trial(manifest, models, output, random_count=1, hard_count=0)
        self.assertFalse(output.exists())

    def test_insufficient_answers_and_existing_output_are_not_silently_reused(self):
        from sse_multivector.distillation_review_trial import prepare_trial
        manifest, models = self.fixture(self.notes(1))
        output = self.root / "trial"
        with self.assertRaisesRegex(ValueError, "not enough"):
            prepare_trial(manifest, models, output, random_count=7, hard_count=0)
        self.assertFalse(output.exists())
        prepare_trial(manifest, models, output, random_count=1, hard_count=0)
        with self.assertRaisesRegex(ValueError, "already exists"):
            prepare_trial(manifest, models, output, random_count=1, hard_count=0)


if __name__ == "__main__":
    unittest.main()
