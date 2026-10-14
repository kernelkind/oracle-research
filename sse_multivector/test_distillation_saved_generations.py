"""Native grader handoff for bounded manual saved generation collections."""
import json
import hashlib
from pathlib import Path
import random
import os
import tempfile
import unittest

from sse_multivector import distillation_review_trial as trial
from sse_multivector import distillation_review_preview as preview
from sse_multivector import distillation_run as run
from sse_multivector import test_distillation_review_preview as fixtures


class DistillationSavedGenerationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def fixture(self, *, name="fixture"):
        fixture = fixtures.DistillationReviewPreviewTests("runTest")
        fixture.root = self.root
        notes = [dict(note_id=f"validation-{i}", post=f"Cable {i}.", teacher=fixtures.TEACHER,
                      answer=fixtures.answer(fixtures.STUDENT)) for i in range(4)]
        manifest, models = fixture.fixture(notes, name=name)
        model = models[0]
        checkpoint = model / "checkpoints/checkpoint-1"
        (checkpoint / "adapter_model.safetensors").write_bytes(
            b"Fixture weight bytes: never needed by an offline review preview.")
        seed = "manual-thinking-fixture"
        policy = dict(enable_thinking=True, thought_budget_tokens=128, final_budget_tokens=256,
                      max_context_tokens=32768, do_sample=False)
        sources = []
        rows = [json.loads(line) for line in (manifest.parent / "evaluation.jsonl").read_text().splitlines()]
        for offset, index in enumerate(sorted(random.Random(seed).sample(range(4), 2))):
            path = self.root / name / f"manual/note-{index:04}/subjects.json"
            saved_answer = fixtures.answer(fixtures.STUDENT) if not offset else fixtures.answer([], raw="unfinished", truncated=True)
            run.write_json(path, dict(note_id=rows[index]["note_id"], messages=rows[index]["messages"],
                answer=saved_answer, generation_policy_sha256=hashlib.sha256(json.dumps(policy,
                    sort_keys=True, separators=(",", ":")).encode()).hexdigest()))
            sources.append(dict(path=str(path), sha256=run.sha256(path), index=index, note_id=rows[index]["note_id"]))
        collection = self.root / name / "manual/collection.json"
        run.write_json(collection, dict(schema_version=1, origin="manual_generations",
            dataset=dict(path=str(manifest), sha256=run.sha256(manifest)),
            model_output=dict(path=str(model), sha256=run.sha256(model / "manifest.json")),
            checkpoint=dict(cursor=1, path=str(checkpoint), sha256=run.sha256(checkpoint / "complete.json")),
            version="checkpoint-1-thinking-on", seed=seed, generation_policy=policy,
            generations=sources, additional_sources={}))
        return fixture, manifest, collection

    def test_native_manual_collection_keeps_original_subset_and_invalid_output(self):
        _, manifest, collection = self.fixture()
        prepared = trial.prepare_trial(manifest, [], self.root / "selection", saved_generations=collection)
        loaded = trial.load_trial(prepared["selection_path"])
        self.assertEqual(len(loaded["random"]["answers"]), 2)
        self.assertEqual(loaded["random"]["totals"]["invalid_outputs"], 1)
        self.assertEqual(loaded["challenge"]["answers"], [])
        self.assertEqual({r["version"] for r in loaded["random"]["answers"]}, {"checkpoint-1-thinking-on"})
        source = run.read_json(collection)
        self.assertEqual([r["generation"]["index"] for r in loaded["random"]["answers"]],
                         [r["index"] for r in source["generations"]])

    def test_native_cli_handoff_prepares_only_imported_answers_without_model_calls(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        fixture, manifest, collection = self.fixture()
        output = self.root / "selection"
        fixture.native("prepare-distillation-review-trial", manifest, "--saved-generations", collection,
                       "--output", output)
        worker = self.root / "fake-runner"
        worker.write_text((fixtures.PROJECT.parent / "experiment-runner/tests/fixtures/fake-runner.py").read_text())
        worker.chmod(0o755)
        destination = self.root / "evaluation"
        calls = self.root / "calls.json"
        fixture.native("prepare-distillation-review-evaluation", output / "selection.json",
            "--output", destination, "--actual-edges-only", "--runner-binary", worker,
            "--reasoning-effort", "high", "--support-reasoning-effort", "medium",
            "--relationship-prompt", fixtures.PROJECT / "sse_multivector/distillation-review-v1/relationship-prompt-v10.md",
            "--relationship-prompt-id", "DSLv10", environment=dict(os.environ, FAKE_RUNNER_LOG=str(calls)))
        report = evaluation.report(destination)
        selected = trial.load_trial(output / "selection.json")
        self.assertEqual({r["id"] for r in report["random"]["answers"]},
                         {r["id"] for r in selected["random"]["answers"]})
        invalid = next(r for r in report["random"]["answers"] if r["errors"])
        self.assertEqual({k: v["value"] for k, v in invalid["scores"].items()}, {"correctness": 0.0, "coverage": 0.0})
        self.assertFalse(calls.exists())

    def test_import_rejects_changed_input_and_wrong_policy_even_with_new_receipt_hash(self):
        for defect in ("input", "policy"):
            with self.subTest(defect=defect):
                _, manifest, collection = self.fixture(name=defect)
                value = run.read_json(collection)
                ref = value["generations"][0]
                path = Path(ref["path"])
                saved = run.read_json(path)
                if defect == "input":
                    saved["messages"][0]["content"] += " Changed input."
                else:
                    saved["generation_policy_sha256"] = "f" * 64
                run.write_json(path, saved)
                ref["sha256"] = run.sha256(path)
                run.write_json(collection, value)
                with self.assertRaisesRegex(ValueError, "input or policy differs"):
                    trial.prepare_trial(manifest, [], self.root / ("selection-" + defect), saved_generations=collection)

    def test_frozen_selection_rejects_edited_saved_response_and_resealed_evidence(self):
        _, manifest, collection = self.fixture()
        report = trial.prepare_trial(manifest, [], self.root / "selection", saved_generations=collection)
        path = Path(report["selection_path"])
        value = run.read_json(path)
        value["random"]["answers"][0]["post"] = "Changed post."
        run.write_json(path, value)
        run.write_json(path.parent / "selection.complete.json", {path.name: run.sha256(path)})
        with self.assertRaisesRegex(ValueError, "selected evidence differs"):
            trial.load_trial(path)
        run.write_json(path, {k: v for k, v in report.items() if k != "selection_path"})
        run.write_json(path.parent / "selection.complete.json", {path.name: run.sha256(path)})
        generation = Path(report["random"]["answers"][0]["generation"]["path"])
        generation.write_bytes(generation.read_bytes() + b"\n")
        with self.assertRaisesRegex(ValueError, "source hash differs"):
            trial.load_trial(path)


if __name__ == "__main__":
    unittest.main()
