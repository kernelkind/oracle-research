"""Offline saved-validation review previews through the native project CLI."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from sse_multivector import distillation_run as run


PROJECT = Path(__file__).resolve().parents[1]
LAUNCHER = PROJECT.parent / "experiment-runner/bin/experiment-runner"
AS = PROJECT / "sse_multivector/subject-prompt-goal-v1/asv6.100/ASv6.100.md"


def subjects(*rows):
    return [dict(number=number, context="Saved fixture context.", subject=wording)
            for number, wording in rows]


TEACHER = subjects(("1", "Cables"), ("1.1", "2 m cable A"), ("1.2", "2 m cable A"),
                   ("1.3", "Cable A is not longer than cable B"), ("2", "Tools"), ("2.1", "Sharp knife"))
STUDENT = subjects(("1", "Cables"), ("1.1", "2 m cable A"), ("1.2", "2 m cable A"),
                   ("1.3", "Cable A is longer than cable B"), ("1.4", "Cable A is longer than cable B"),
                   ("2", "Tools"), ("2.1", "2 m cable A"), ("3", "New heading"),
                   ("3.1", "New heading"), ("4", "Cable A"), ("5", "cables"))


def answer(rows, *, raw=None, truncated=False):
    return dict(raw=json.dumps(dict(subjects=rows)) if raw is None else raw,
                tokens=40, truncated=truncated)


class DistillationReviewPreviewTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def fixture(self, notes=None, *, name="fixture", models=1):
        root = self.root / name
        prepared = root / "prepared"
        prepared.mkdir(parents=True)
        if notes is None:
            notes = [dict(note_id="validation-a", post="Cable A is 2 m long and is not longer than cable B.",
                          teacher=TEACHER, answer=answer(STUDENT))]
        task = AS.read_text()
        evaluation = [dict(note_id=note["note_id"], messages=[dict(role="user",
            content=task + "\n\n<post>\n" + note["post"] + "\n</post>")]) for note in notes]
        references = [dict(note_id=note["note_id"], split="evaluation", text=note["post"],
                           subjects=note["teacher"]) for note in notes]
        # Only the note_id headers of other splits may be inspected. Their
        # contents deliberately cannot be decoded as JSON or subject answers.
        reference_lines = ['{"note_id":"train-a", "poison": INVALID TRAIN CONTENT}']
        reference_lines.extend(json.dumps(row) for row in references)
        reference_lines.append('{"note_id":"test-a", "poison": INVALID RESERVED CONTENT}')
        (prepared / "references.jsonl").write_text("\n".join(reference_lines) + "\n")
        (prepared / "evaluation.jsonl").write_text("\n".join(json.dumps(row) for row in evaluation) + "\n")
        manifest = dict(schema_version=2, tasks=dict(subjects="ASv6.100"),
            train_note_ids=["train-a"], evaluation_note_ids=[note["note_id"] for note in notes],
            test_note_ids=["test-a"], subject_instruction_sha256=hashlib.sha256(task.encode()).hexdigest(),
            outputs={name: run.sha256(prepared / name) for name in ("evaluation.jsonl", "references.jsonl")})
        manifest["outputs"].update({name: "f" * 64 for name in ("train.jsonl", "test.jsonl")})
        run.write_json(prepared / "manifest.json", manifest)
        model_outputs = []
        for index in range(models):
            output = root / f"model-{index}"
            config = dict(model=f"fixture/model-{index}", revision=str(index + 1) * 40,
                data=str(prepared), training_milestones=[1], evaluation_tasks=["subjects"],
                max_new_tokens=dict(subjects=64), subject_batching=dict(budget_bytes=4096,
                    workspace_bytes=0, prefill_bytes_per_token=1, attention_matrix_count=4))
            run.write_json(output / "manifest.json", dict(config=config, dataset=manifest))
            plan = dict(note_ids=["train-a"], milestones=[1], examples_per_update=8)
            run.write_json(output / "training-plan.json", plan)
            run.seal_files(output, "provenance.complete.json", ["manifest.json", "training-plan.json"])
            checkpoint = output / "checkpoints/checkpoint-1"
            run.write_json(checkpoint / "training.json", dict(cursor=1, updates=1,
                consumed_note_ids=["train-a"], manifest_sha256=run.sha256(output / "manifest.json"),
                plan_sha256=run.sha256(output / "training-plan.json")))
            weight = checkpoint / "adapter_model.safetensors"
            weight.write_bytes(b"Fixture weight bytes: never needed by an offline review preview.")
            run.write_json(checkpoint / "complete.json", run.file_hashes(checkpoint))
            weight.write_bytes(b"Changed weight bytes prove the preview does not hash weights.")
            for relative in ("baseline", "evaluations/checkpoint-1"):
                self.stage(output / relative, evaluation, [note["answer"] for note in notes])
            (output / "test").mkdir()
            (output / "test/poison").write_text("Reserved saved generations must not be read.")
            model_outputs.append(output)
        return prepared / "manifest.json", model_outputs

    def stage(self, directory, evaluation, answers):
        batch = dict(indices=list(range(len(evaluation))), prompt_width=1, estimated_bytes=100)
        plan = dict(policy={}, memory={}, max_new_tokens=64,
            inputs=[dict(note_id=row["note_id"], tokens=1, sha256="e" * 64) for row in evaluation],
            batches=[batch])
        run.write_json(directory / "subject-batches.json", plan)
        receipt = dict(batch=batch, note_ids=[row["note_id"] for row in evaluation],
            messages=[row["messages"] for row in evaluation], input_tokens=[1] * len(evaluation),
            answers=answers, seconds=1.)
        run.write_json(directory / "subjects-0000.json", receipt)
        results = []
        for index, (row, saved_answer) in enumerate(zip(evaluation, answers)):
            note = directory / f"note-{index:04}"
            parsed = run.subject_result(row["note_id"], saved_answer)
            run.write_json(note / "subjects.json", dict(note_id=row["note_id"], messages=row["messages"],
                answer=saved_answer, batch=dict(file="subjects-0000.json", offset=index)))
            run.write_json(note / "subjects-result.json", parsed)
            run.write_json(note / "complete.json", run.file_hashes(note))
            results.append(dict(parsed, masks=[]))
        run.write_json(directory / "results.json", results)
        run.write_json(directory / "complete.json", run.file_hashes(directory))
        # Validate the fixture with the real saved-stage verifier before preview.
        self.assertEqual(run.subject_stage_summary(directory, dict(evaluation=evaluation))["notes"], len(evaluation))

    def preview(self, manifest, outputs):
        from sse_multivector import distillation_review_preview
        return distillation_review_preview.preview(manifest, outputs)

    def check(self, totals, name, occurrences, mechanical, semantic, distinct, rules):
        self.assertEqual(totals["checks"][name], dict(occurrences=occurrences, mechanical=mechanical,
            semantic=semantic, distinct_semantic_inputs=distinct, mechanical_rules=rules))

    def test_native_command_help_exposes_offline_preview(self):
        result = subprocess.run([str(LAUNCHER), "--project-root", str(PROJECT),
            "preview-distillation-review", "--help"], cwd=PROJECT,
            capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("--model-output", result.stdout)
        self.assertIn("--output", result.stdout)

    def test_native_cli_previews_multiple_models_without_changing_sources(self):
        manifest, outputs = self.fixture(models=2)
        before = run.file_hashes(manifest.parent.parent)
        report_path = self.root / "preview.json"
        command = [str(LAUNCHER), "--project-root", str(PROJECT), "preview-distillation-review", str(manifest)]
        for output in outputs:
            command.extend(["--model-output", str(output)])
        result = subprocess.run([*command, "--output", str(report_path)], cwd=PROJECT,
            capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(report_path.read_text())
        self.assertEqual(report["schema_version"], 1)
        self.assertEqual(report["inference_calls"], 0)
        self.assertIn("before saved-answer reuse", report["distinct_input_basis"])
        self.assertIn("unprepared", report["distinct_input_basis"])
        self.assertEqual(report["dataset"], dict(path=str(manifest), sha256=run.sha256(manifest)))
        self.assertEqual(report["totals"]["versions"], 4)
        self.assertEqual(report["totals"]["subject_occurrences"], 44)
        self.assertEqual(len(report["models"]), 2)
        self.assertIn("mechanical", result.stdout)
        self.assertIn("semantic", result.stdout)
        self.assertEqual(before, run.file_hashes(manifest.parent.parent))
        for path, digest in report["sources"].items():
            self.assertTrue(Path(path).is_absolute())
            self.assertEqual(run.sha256(path), digest)
            self.assertNotIn(Path(path).name, {"train.jsonl", "test.jsonl", "adapter_model.safetensors"})
            self.assertNotIn("test", Path(path).parts)

    def test_occurrences_use_exact_teacher_subjects_and_actual_ordered_edges(self):
        manifest, outputs = self.fixture()
        report = self.preview(manifest, outputs)
        model = report["models"][0]
        self.assertEqual(model["model"], "fixture/model-0")
        self.assertEqual(model["revision"], "1" * 40)
        self.assertEqual([version["version"] for version in model["versions"]], ["baseline", "checkpoint-1"])
        stage = model["versions"][0]
        totals = stage["totals"]
        self.assertEqual(totals["versions"], 1)
        self.assertEqual(totals["outputs"], 1)
        self.assertEqual(totals["valid_outputs"], 1)
        self.assertEqual(totals["invalid_outputs"], 0)
        self.assertEqual(totals["empty_outputs"], 0)
        self.assertEqual(totals["subject_occurrences"], 11)
        self.assertEqual(totals["relationship_occurrences"], 6)
        for check in ("matching", "support"):
            self.check(totals, check, 11, 5, 6, 4, dict(exact_teacher_subject=5))
        self.check(totals, "relationship", 6, 3, 3, 2,
                   dict(exact_teacher_relationship=2, identical_subjects=1))
        self.assertEqual(stage["notes"][0]["note_id"], "validation-a")
        self.assertEqual(stage["notes"][0]["totals"], dict(totals, versions=0))
        self.assertEqual(report["totals"], model["totals"])
        self.check(report["totals"], "matching", 22, 10, 12, 4, dict(exact_teacher_subject=10))
        self.check(report["totals"], "support", 22, 10, 12, 4, dict(exact_teacher_subject=10))
        self.check(report["totals"], "relationship", 12, 6, 6, 2,
                   dict(exact_teacher_relationship=4, identical_subjects=2))

    def test_distinct_semantic_inputs_preserve_full_check_input(self):
        changed = "Cable A is longer than cable B"
        student = subjects(("1", "Cables"), ("1.1", changed))
        teacher = subjects(("1", "Cables"), ("1.1", "Cable A is not longer than cable B"))
        notes = [dict(note_id="validation-a", post="Cable A is not longer than cable B.",
                      teacher=teacher, answer=answer(student)),
                 dict(note_id="validation-b", post="Cable A is not longer than cable B.",
                      teacher=subjects(("1", "Cables"), ("1.1", "3 m cable B")), answer=answer(student)),
                 dict(note_id="validation-c", post="At today's demonstration, cable A is not longer than cable B.",
                      teacher=teacher, answer=answer(student))]
        manifest, outputs = self.fixture(notes, models=2)
        report = self.preview(manifest, outputs)
        self.check(report["totals"], "matching", 24, 12, 12, 3, dict(exact_teacher_subject=12))
        self.check(report["totals"], "support", 24, 12, 12, 2, dict(exact_teacher_subject=12))
        self.check(report["totals"], "relationship", 12, 0, 12, 1, {})

    def test_invalid_truncated_and_empty_outputs_remain_separate(self):
        teacher = subjects(("1", "Cables"))
        notes = [dict(note_id="valid", post="Cables.", teacher=teacher, answer=answer(teacher)),
                 dict(note_id="empty", post="Cables.", teacher=teacher, answer=answer([])),
                 dict(note_id="malformed", post="Cables.", teacher=teacher, answer=answer([], raw="not JSON")),
                 dict(note_id="truncated", post="Cables.", teacher=teacher, answer=answer(teacher, truncated=True))]
        manifest, outputs = self.fixture(notes)
        report = self.preview(manifest, outputs)
        totals = report["totals"]
        for key, count in dict(versions=2, outputs=8, valid_outputs=4, invalid_outputs=4,
                              empty_outputs=2, subject_occurrences=2, relationship_occurrences=0).items():
            self.assertEqual(totals[key], count, key)
        for check in ("matching", "support"):
            self.check(totals, check, 2, 2, 0, 0, dict(exact_teacher_subject=2))
        self.check(totals, "relationship", 0, 0, 0, 0, {})
        notes = {note["note_id"]: note["totals"] for note in report["models"][0]["versions"][0]["notes"]}
        self.assertEqual(notes["empty"]["empty_outputs"], 1)
        for identifier in ("malformed", "truncated"):
            self.assertEqual(notes[identifier]["invalid_outputs"], 1)
            self.assertEqual(notes[identifier]["subject_occurrences"], 0)

    def test_valid_empty_teacher_catalog_only_decides_matching(self):
        student = subjects(("1", "New heading"), ("1.1", "New heading"))
        manifest, outputs = self.fixture([dict(note_id="validation-a", post="A post without teacher subjects.",
                                               teacher=[], answer=answer(student))])
        totals = self.preview(manifest, outputs)["totals"]
        self.check(totals, "matching", 4, 4, 0, 0, dict(empty_teacher_catalog=4))
        self.check(totals, "support", 4, 0, 4, 1, {})
        self.check(totals, "relationship", 2, 2, 0, 0, dict(identical_subjects=2))

    def test_saved_stage_receipts_are_verified_after_resealing(self):
        manifest, outputs = self.fixture()
        stage = outputs[0] / "baseline"
        receipt = run.read_json(stage / "subjects-0000.json")
        receipt["answers"] = []
        run.write_json(stage / "subjects-0000.json", receipt)
        run.write_json(stage / "complete.json", run.file_hashes(stage))
        with self.assertRaisesRegex(ValueError, "receipt"):
            self.preview(manifest, outputs)

    def test_saved_parsed_result_cannot_override_original_answer(self):
        manifest, outputs = self.fixture()
        stage = outputs[0] / "baseline"
        parsed = dict(note_id="validation-a", subjects=[], errors=[])
        run.write_json(stage / "note-0000/subjects-result.json", parsed)
        run.write_json(stage / "results.json", [dict(parsed, masks=[])])
        run.write_json(stage / "note-0000/complete.json", run.file_hashes(stage / "note-0000"))
        run.write_json(stage / "complete.json", run.file_hashes(stage))
        with self.assertRaisesRegex(ValueError, "parsed subject result differs from raw"):
            self.preview(manifest, outputs)

    def test_frozen_dataset_model_provenance_and_checkpoint_bindings_are_required(self):
        for defect in ("dataset_hash", "embedded_dataset", "provenance", "checkpoint_training", "missing_stage"):
            with self.subTest(defect=defect):
                manifest, outputs = self.fixture(name=defect)
                output = outputs[0]
                if defect == "dataset_hash":
                    with (manifest.parent / "evaluation.jsonl").open("a") as stream:
                        stream.write("\n")
                elif defect == "embedded_dataset":
                    frozen = run.read_json(output / "manifest.json")
                    frozen["dataset"]["subject_instruction_sha256"] = "0" * 64
                    run.write_json(output / "manifest.json", frozen)
                    run.write_json(output / "provenance.complete.json",
                        {name: run.sha256(output / name) for name in ("manifest.json", "training-plan.json")})
                elif defect == "provenance":
                    frozen = run.read_json(output / "manifest.json")
                    frozen["config"]["revision"] = "0" * 40
                    run.write_json(output / "manifest.json", frozen)
                elif defect == "checkpoint_training":
                    checkpoint = output / "checkpoints/checkpoint-1"
                    training = run.read_json(checkpoint / "training.json")
                    training["cursor"] = 2
                    run.write_json(checkpoint / "training.json", training)
                    seal = run.read_json(checkpoint / "complete.json")
                    seal["training.json"] = run.sha256(checkpoint / "training.json")
                    run.write_json(checkpoint / "complete.json", seal)
                else:
                    shutil.rmtree(output / "evaluations/checkpoint-1")
                with self.assertRaises((ValueError, FileNotFoundError)):
                    self.preview(manifest, outputs)

    def test_all_reference_headers_are_checked_before_evaluation_content_is_decoded(self):
        manifest, outputs = self.fixture()
        path = manifest.parent / "references.jsonl"
        lines = path.read_text().splitlines()
        lines[1] = '{"note_id":"validation-a", "poison": INVALID EVALUATION CONTENT}'
        lines[-1] = '{"note_id":"unknown-test", "poison": INVALID RESERVED CONTENT}'
        path.write_text("\n".join(lines) + "\n")
        dataset = run.read_json(manifest)
        dataset["outputs"][path.name] = run.sha256(path)
        run.write_json(manifest, dataset)
        with self.assertRaisesRegex(ValueError, "reference"):
            self.preview(manifest, outputs)


if __name__ == "__main__":
    unittest.main()
