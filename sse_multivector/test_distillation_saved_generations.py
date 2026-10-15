"""Native grader handoff for manual saved generation collections."""
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
        config = run.read_json(model / "manifest.json")["config"]
        sources = []
        rows = [json.loads(line) for line in (manifest.parent / "evaluation.jsonl").read_text().splitlines()]
        for offset, index in enumerate(sorted(random.Random(seed).sample(range(4), 2))):
            path = self.root / name / f"manual/note-{index:04}/subjects.json"
            saved_answer = fixtures.answer(fixtures.STUDENT) if not offset else fixtures.answer([], raw="unfinished", truncated=True)
            run.write_json(path, dict(note_id=rows[index]["note_id"], messages=rows[index]["messages"],
                model=config["model"], revision=config["revision"],
                checkpoint_sha256=run.sha256(checkpoint / "complete.json"),
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

    def directory_fixture(self, *, name="directory"):
        fixture, manifest, collection = self.fixture(name=name)
        value = run.read_json(collection)
        directory = collection.parent
        policy = dict(value["generation_policy"], do_sample=True, stop_policy="natural_eos",
                      thought_budget_tokens=None, final_budget_tokens=None, temperature=1.0)
        notes = []
        for reference in value["generations"]:
            saved = run.read_json(reference["path"])
            notes.append(dict(index=reference["index"], note_id=saved["note_id"], messages=saved["messages"]))
        inputs = dict(schema_version=1, seed=value["seed"], model=saved["model"], revision=saved["revision"],
            dataset_sha256=value["dataset"]["sha256"], checkpoint=1,
            checkpoint_sha256=value["checkpoint"]["sha256"], notes=notes,
            checkpoint_files={"adapter_model.safetensors": run.sha256(
                Path(value["checkpoint"]["path"]) / "adapter_model.safetensors")},
            generation_policy=value["generation_policy"])
        original = directory / "original-inputs.json"
        run.write_json(original, inputs)
        inputs = dict(inputs, generation_policy=policy, reused_generations=[],
            original_inputs=dict(path=original.name, sha256=run.sha256(original)))
        run.write_json(directory / "inputs.json", inputs)
        source = directory / "actual-driver.py"
        source.write_text("# Saved generating source; ingestion never executes it.\n")
        runtime = directory / "runtime.json"
        run.write_json(runtime, dict(model=inputs["model"], revision=inputs["revision"],
            checkpoint_sha256=inputs["checkpoint_sha256"], input_sha256=run.sha256(directory / "inputs.json"),
            generation_policy=policy, script_sha256=run.sha256(source)))
        marker = {}
        for reference in value["generations"]:
            saved = run.read_json(reference["path"])
            saved.update(index=reference["index"], generation_policy_sha256=hashlib.sha256(json.dumps(policy,
                sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
                runtime_receipt=dict(path=runtime.name, sha256=run.sha256(runtime)))
            path = directory / "generations" / f"note-{reference['index']:04}" / "subjects.json"
            run.write_json(path, saved)
            marker[str(path.relative_to(directory))] = run.sha256(path)
        run.write_json(directory / "generation.complete.json", marker)
        return fixture, manifest, Path(value["model_output"]["path"]), directory, source

    def test_native_directory_import_freezes_complete_sources_without_handmade_index(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        fixture, manifest, model, directory, source = self.directory_fixture()
        original = {str(p): run.sha256(p) for p in directory.rglob("subjects.json")}
        destination = self.root / "selection"
        fixture.native("prepare-distillation-review-trial", manifest, "--model-output", model,
            "--saved-generations", directory, "--generation-version", "checkpoint-1-thinking-on-sampled",
            "--generation-source", source, "--output", destination)
        loaded = trial.load_trial(destination / "selection.json")
        self.assertEqual(len(loaded["random"]["answers"]), 2)
        self.assertEqual(loaded["random"]["totals"]["invalid_outputs"], 1)
        self.assertTrue(loaded["generation_policy"]["do_sample"])
        self.assertEqual({row["version"] for row in loaded["random"]["answers"]}, {"checkpoint-1-thinking-on-sampled"})
        for path in (directory / "inputs.json", directory / "generation.complete.json",
                     directory / "runtime.json", directory / "original-inputs.json", source):
            self.assertEqual(loaded["sources"][str(path)], run.sha256(path))
        self.assertEqual({p: run.sha256(p) for p in original}, original)
        worker = self.root / "fake-runner"
        worker.write_text((fixtures.PROJECT.parent / "experiment-runner/tests/fixtures/fake-runner.py").read_text())
        worker.chmod(0o755)
        calls = self.root / "calls.json"
        fixture.native("prepare-distillation-review-evaluation", destination / "selection.json",
            "--output", self.root / "evaluation", "--actual-edges-only", "--runner-binary", worker,
            "--reasoning-effort", "high", "--support-reasoning-effort", "medium",
            "--relationship-prompt", fixtures.PROJECT / "sse_multivector/distillation-review-v1/relationship-prompt-v10.md",
            "--relationship-prompt-id", "DSLv10", environment=dict(os.environ, FAKE_RUNNER_LOG=str(calls)))
        report = evaluation.report(self.root / "evaluation")
        self.assertEqual({r["id"] for r in report["random"]["answers"]},
                         {r["id"] for r in loaded["random"]["answers"]})
        invalid = next(r for r in report["random"]["answers"] if r["errors"])
        self.assertEqual({k: v["value"] for k, v in invalid["scores"].items()}, {"correctness": 0.0, "coverage": 0.0})
        self.assertFalse(calls.exists())
        marker = directory / "generation.complete.json"
        marker.write_bytes(marker.read_bytes() + b"\n")
        with self.assertRaisesRegex(ValueError, "trial source hash differs"):
            trial.load_trial(destination / "selection.json")

    def test_directory_import_rejects_missing_or_changed_receipts_without_publishing_selection(self):
        for defect in ("incomplete", "response", "runtime", "input", "checkpoint", "cohort"):
            with self.subTest(defect=defect):
                _, manifest, model, directory, source = self.directory_fixture(name=defect)
                marker = directory / "generation.complete.json"
                mapping = run.read_json(marker)
                if defect == "incomplete":
                    del mapping[next(iter(mapping))]
                    run.write_json(marker, mapping)
                elif defect == "response":
                    path = directory / next(iter(mapping))
                    path.write_bytes(path.read_bytes() + b"\n")
                elif defect == "runtime":
                    path = directory / "runtime.json"
                    path.write_bytes(path.read_bytes() + b"\n")
                elif defect == "input":
                    value = run.read_json(directory / "inputs.json")
                    value["notes"][0]["messages"][0]["content"] += " Changed."
                    run.write_json(directory / "inputs.json", value)
                elif defect == "checkpoint":
                    checkpoint = model / "checkpoints/checkpoint-1/adapter_model.safetensors"
                    checkpoint.write_bytes(b"Changed weight bytes.")
                else:
                    # A self-consistent smaller cohort must still preserve the
                    # original seed's sample, rather than selecting by completion.
                    value = run.read_json(directory / "inputs.json")
                    chosen = list(mapping)[-1]
                    value["notes"] = value["notes"][-1:]
                    del value["original_inputs"]
                    run.write_json(directory / "inputs.json", value)
                    runtime = run.read_json(directory / "runtime.json")
                    runtime["input_sha256"] = run.sha256(directory / "inputs.json")
                    run.write_json(directory / "runtime.json", runtime)
                    saved = run.read_json(directory / chosen)
                    saved["runtime_receipt"]["sha256"] = run.sha256(directory / "runtime.json")
                    run.write_json(directory / chosen, saved)
                    for filename in mapping:
                        if filename != chosen:
                            (directory / filename).unlink()
                    run.write_json(marker, {chosen: run.sha256(directory / chosen)})
                output = self.root / ("selection-" + defect)
                with self.assertRaisesRegex(ValueError, "seeded validation sample" if defect == "cohort" else ".*"):
                    trial.prepare_trial(manifest, [model], output, saved_generations=directory,
                        generation_version="checkpoint-1-thinking-on-sampled", generation_sources=[source])
                self.assertFalse(output.exists())

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

    def test_mixed_generation_policies_preserve_original_receipts(self):
        for natural_default in (False, True):
            with self.subTest(natural_default=natural_default):
                name = f"mixed-{natural_default}"
                _, manifest, collection = self.fixture(name=name)
                value = run.read_json(collection)
                legacy = value["generation_policy"]
                natural = dict(legacy, thought_budget_tokens=None, final_budget_tokens=None,
                               stop_policy="natural_eos", max_context_tokens=262144)
                first, second = value["generations"]
                original = Path(first["path"]).read_bytes()
                if natural_default:
                    value["generation_policy"] = natural
                    first["generation_policy"] = legacy
                else:
                    second["generation_policy"] = natural
                path = Path(second["path"])
                saved = run.read_json(path)
                saved["generation_policy_sha256"] = hashlib.sha256(json.dumps(natural,
                    sort_keys=True, separators=(",", ":")).encode()).hexdigest()
                run.write_json(path, saved)
                second["sha256"] = run.sha256(path)
                run.write_json(collection, value)
                prepared = trial.prepare_trial(manifest, [], self.root / ("selection-" + name),
                                               saved_generations=collection)
                loaded = trial.load_trial(prepared["selection_path"])
                self.assertEqual(loaded["generation_policy"], value["generation_policy"])
                self.assertEqual([r["generation"] for r in loaded["random"]["answers"]], value["generations"])
                self.assertEqual(loaded["random"]["totals"]["invalid_outputs"], 1)
                self.assertEqual(Path(first["path"]).read_bytes(), original)
                self.assertEqual(run.sha256(first["path"]), first["sha256"])

    def test_policy_override_cannot_relabel_a_saved_generation(self):
        _, manifest, collection = self.fixture()
        value = run.read_json(collection)
        value["generations"][0]["generation_policy"] = dict(value["generation_policy"],
            thought_budget_tokens=None, final_budget_tokens=None,
            stop_policy="natural_eos", max_context_tokens=262144)
        run.write_json(collection, value)
        with self.assertRaisesRegex(ValueError, "input or policy differs"):
            trial.prepare_trial(manifest, [], self.root / "selection", saved_generations=collection)

    def test_natural_eos_policy_rejects_phase_caps_and_unknown_modes(self):
        defects = ({"stop_policy": "unknown"}, {"stop_policy": "natural_eos"},
                   {"thought_budget_tokens": None, "final_budget_tokens": None},
                   {"stop_policy": "natural_eos", "thought_budget_tokens": None},
                   {"stop_policy": "natural_eos", "thought_budget_tokens": None,
                    "final_budget_tokens": None, "do_sample": 0})
        for index, defect in enumerate(defects):
            with self.subTest(defect=defect):
                _, manifest, collection = self.fixture(name=f"invalid-policy-{index}")
                value = run.read_json(collection)
                value["generation_policy"].update(defect)
                run.write_json(collection, value)
                with self.assertRaisesRegex(ValueError, "invalid manual generation policy"):
                    trial.prepare_trial(manifest, [], self.root / f"selection-{index}", saved_generations=collection)

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

    def test_import_rejects_wrong_checkpoint_when_policy_and_receipt_hash_match(self):
        _, manifest, collection = self.fixture()
        value = run.read_json(collection)
        ref = value["generations"][0]
        path = Path(ref["path"])
        saved = run.read_json(path)
        saved["checkpoint_sha256"] = "f" * 64
        run.write_json(path, saved)
        ref["sha256"] = run.sha256(path)
        run.write_json(collection, value)
        with self.assertRaisesRegex(ValueError, "model or checkpoint differs"):
            trial.prepare_trial(manifest, [], self.root / "selection", saved_generations=collection)


if __name__ == "__main__":
    unittest.main()
