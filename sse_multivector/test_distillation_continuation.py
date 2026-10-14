"""Continuation contracts use the production planner and checkpoint verifier."""
import copy
from pathlib import Path
import tempfile
import unittest

from sse_multivector import distillation_run as run


class ContinuationContractTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.parent = Path(self.temporary.name) / "parent"
        self.parent.mkdir()
        self.data = {"train": [{"note_id": str(i), "task": "subjects"} for i in range(8)],
                     "manifest": {"tasks": ["subjects"], "train_note_ids": list(map(str, range(8)))}}
        self.original = {"model": "fixture/qwen", "revision": "a" * 40, "seed": 17,
                         "batch_size": 1, "gradient_accumulation_steps": 8,
                         "learning_rate": .0001, "training_milestones": [4, 8],
                         "evaluation_tasks": ["subjects"]}
        run.write_json(self.parent / "manifest.json", {"config": self.original,
                       "dataset": self.data["manifest"], "local_model": None})
        self.parent_plan = run.save_subject_training_plan(self.data, self.original, self.parent)
        checkpoint = self.parent / "checkpoints/checkpoint-8"
        checkpoint.mkdir(parents=True)
        for name in ("adapter_config.json", "adapter_model.safetensors", "training-state.pt"):
            (checkpoint / name).write_bytes(b"sealed checkpoint fixture")
        run.write_json(checkpoint / "training.json", {
            "cursor": 8, "updates": 2, "supervised_tokens": 32,
            "consumed_note_ids": self.parent_plan["note_ids"],
            "manifest_sha256": run.sha256(self.parent / "manifest.json"),
            "plan_sha256": run.sha256(self.parent / "training-plan.json")})
        run.write_json(checkpoint / "complete.json", run.file_hashes(checkpoint))
        self.config = {**self.original, "training_milestones": [16, 24], "continuation": {
            "parent_run": str(self.parent),
            "manifest_sha256": run.sha256(self.parent / "manifest.json"),
            "plan_sha256": run.sha256(self.parent / "training-plan.json"),
            "checkpoint_sha256": run.sha256(checkpoint / "complete.json")}}

    def test_plan_preserves_parent_order_and_adds_two_complete_passes(self):
        plan = run.subject_training_plan(self.data, self.config)
        self.assertEqual(plan["note_ids"][:8], self.parent_plan["note_ids"])
        self.assertEqual(plan["milestones"], [4, 8, 16, 24])
        for start in (8, 16):
            self.assertCountEqual(plan["note_ids"][start:start + 8], list(map(str, range(8))))
        self.assertEqual(plan, run.subject_training_plan(self.data, self.config))
        self.assertNotEqual(plan["note_ids"][8:16], plan["note_ids"][16:24])

    def test_parent_files_and_original_recipe_cannot_change(self):
        for key in ("manifest_sha256", "plan_sha256", "checkpoint_sha256"):
            config = copy.deepcopy(self.config)
            config["continuation"][key] = "0" * 64
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "parent"):
                run.subject_training_plan(self.data, config)
        for key, value in (("learning_rate", .001), ("revision", "b" * 40),
                           ("model", "fixture/other"), ("evaluation_tasks", ["subjects", "mask"])):
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "recipe"):
                run.subject_training_plan(self.data, {**self.config, key: value})

    def test_continuation_requires_complete_passes_and_unchanged_dataset(self):
        for milestones in ([9, 24], [16, 23], [16, 16], []):
            with self.subTest(milestones=milestones), self.assertRaisesRegex(ValueError, "complete passes"):
                run.subject_training_plan(self.data, {**self.config, "training_milestones": milestones})
        data = copy.deepcopy(self.data)
        data["manifest"]["train_note_ids"][0] = "changed"
        with self.assertRaisesRegex(ValueError, "dataset"):
            run.subject_training_plan(data, self.config)


if __name__ == "__main__":
    unittest.main()
