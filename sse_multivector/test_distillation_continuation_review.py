"""Saved continuation grading keeps parent identity and test selection explicit."""
import copy
from pathlib import Path
import shutil
import tempfile
import unittest

from sse_multivector import distillation_run as run
from sse_multivector import distillation_review_trial as trial
from sse_multivector import test_distillation_review_preview as fixtures


class ContinuationReviewTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.fixture = fixtures.DistillationReviewPreviewTests("runTest")
        self.fixture.root = self.root

    def continuation(self, *, split="evaluation"):
        manifest, outputs = self.fixture.fixture(split=split)
        parent = outputs[0]
        saved = run.read_json(parent / "manifest.json")
        original = saved["config"]
        original.update(seed=17, batch_size=1, gradient_accumulation_steps=8)
        run.write_json(parent / "manifest.json", saved)
        (parent / "provenance.complete.json").unlink()
        run.seal_files(parent, "provenance.complete.json", ["manifest.json", "training-plan.json"])
        checkpoint = parent / "checkpoints/checkpoint-1"
        metadata = run.read_json(checkpoint / "training.json")
        metadata["manifest_sha256"] = run.sha256(parent / "manifest.json")
        run.write_json(checkpoint / "training.json", metadata)
        for name in ("training-state.pt", "adapter_config.json"):
            (checkpoint / name).write_bytes(b"Sealed fixture checkpoint state")
        run.write_json(checkpoint / "complete.json", run.file_hashes(checkpoint))
        config = {**original, "training_milestones": [2, 3], "continuation": dict(
            parent_run=str(parent), manifest_sha256=run.sha256(parent / "manifest.json"),
            plan_sha256=run.sha256(parent / "training-plan.json"),
            checkpoint_sha256=run.sha256(checkpoint / "complete.json"))}
        data = dict(manifest=saved["dataset"], train=[dict(note_id="train-a", task="subjects")])
        plan = run.subject_training_plan(data, config)
        # The saved rental path is unavailable locally; the explicit parent
        # resolves it without rewriting any frozen training provenance.
        config = copy.deepcopy(config)
        config["continuation"]["parent_run"] = "/unavailable/rental/parent"
        output = self.root / "continuation"
        run.write_json(output / "manifest.json", dict(config=config, dataset=saved["dataset"]))
        run.write_json(output / "training-plan.json", plan)
        run.seal_files(output, "provenance.complete.json", ["manifest.json", "training-plan.json"])
        for cursor in (2, 3):
            destination = output / f"checkpoints/checkpoint-{cursor}"
            shutil.copytree(checkpoint, destination)
            run.write_json(destination / "training.json", dict(cursor=cursor, updates=cursor,
                consumed_note_ids=plan["note_ids"][:cursor],
                manifest_sha256=run.sha256(output / "manifest.json"),
                plan_sha256=run.sha256(output / "training-plan.json")))
            run.write_json(destination / "complete.json", run.file_hashes(destination))
            source = parent / ("test/checkpoint-1" if split == "test" else "evaluations/checkpoint-1")
            stage = output / (f"test/checkpoint-{cursor}" if split == "test" else f"evaluations/checkpoint-{cursor}")
            shutil.copytree(source, stage)
            if split == "test":
                run.write_json(stage / "test-collection.json", run.subject_test_source(output, destination))
                run.write_json(stage / "complete.json", run.file_hashes(stage))
        return manifest, output, parent

    def test_native_validation_selection_roundtrips_both_added_passes(self):
        manifest, output, parent = self.continuation()
        rows = [run.read_json(manifest.parent / "evaluation.jsonl")]
        self.fixture.stage(output / "evaluations/checkpoint-2", rows,
                           [fixtures.answer([], raw="saved invalid answer")])
        destination = self.root / "selection"
        self.fixture.native("prepare-distillation-review-trial", manifest,
            "--model-output", output, "--parent-run", parent,
            "--random-count", "2", "--hard-count", "0", "--output", destination)
        selected = trial.load_trial(destination / "selection.json")
        self.assertEqual({a["version"] for a in selected["random"]["answers"]},
                         {"checkpoint-2", "checkpoint-3"})
        self.assertEqual(selected["model_outputs"][0]["parent_run"], str(parent))
        self.assertFalse(any("/test/" in name for name in selected["sources"]))
        self.assertEqual(selected["random"]["totals"]["invalid_outputs"], 1)
        invalid = next(a for a in selected["random"]["answers"] if a["errors"])
        self.assertEqual(invalid["raw_answer"]["raw"], "saved invalid answer")

    def test_selected_test_checkpoint_does_not_open_other_checkpoint(self):
        manifest, output, parent = self.continuation(split="test")
        (output / "test/checkpoint-3/results.json").write_text("SEALED: do not open")
        selected = trial.prepare_trial(manifest, [output], self.root / "selection", split="test",
            random_count=1, hard_count=0, parent_run=parent, model_versions=["checkpoint-2"])
        loaded = trial.load_trial(selected["selection_path"])
        self.assertEqual([a["version"] for a in loaded["random"]["answers"]], ["checkpoint-2"])
        self.assertFalse(any("/test/checkpoint-3/" in name for name in loaded["sources"]))

    def test_continuation_test_requires_explicit_checkpoint(self):
        manifest, output, parent = self.continuation(split="test")
        with self.assertRaisesRegex(ValueError, "explicit.*checkpoint"):
            trial.prepare_trial(manifest, [output], self.root / "selection", split="test",
                random_count=1, hard_count=0, parent_run=parent)

    def test_resealed_wrong_parent_and_training_order_are_rejected(self):
        from sse_multivector import distillation_review_preview as preview
        manifest, output, parent = self.continuation()
        saved = run.read_json(output / "manifest.json")
        saved["config"]["continuation"]["checkpoint_sha256"] = "0" * 64
        run.write_json(output / "manifest.json", saved)
        run.write_json(output / "provenance.complete.json", {name: run.sha256(output / name)
            for name in ("manifest.json", "training-plan.json")})
        with self.assertRaisesRegex(ValueError, "parent checkpoint"):
            preview.preview(manifest, [output], parent_run=parent)
        saved["config"]["continuation"]["checkpoint_sha256"] = run.sha256(parent / "checkpoints/checkpoint-1/complete.json")
        run.write_json(output / "manifest.json", saved)
        plan = run.read_json(output / "training-plan.json")
        plan["note_ids"][-1] = "unknown-training-note"
        run.write_json(output / "training-plan.json", plan)
        run.write_json(output / "provenance.complete.json", {name: run.sha256(output / name)
            for name in ("manifest.json", "training-plan.json")})
        with self.assertRaisesRegex(ValueError, "training plan"):
            preview.preview(manifest, [output], parent_run=parent)


if __name__ == "__main__":
    unittest.main()
