"""Offline saved-validation review previews through the native project CLI."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

import tiktoken

from sse_multivector import distillation_run as run
from sse_multivector.experiment_inputs import render


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

    def fixture(self, notes=None, *, name="fixture", models=1, split="evaluation", milestones=(1,)):
        root = self.root / name
        prepared = root / "prepared"
        prepared.mkdir(parents=True)
        if notes is None:
            notes = [dict(note_id="validation-a", post="Cable A is 2 m long and is not longer than cable B.",
                          teacher=TEACHER, answer=answer(STUDENT))]
        task = AS.read_text()
        evaluation = [dict(note_id=note["note_id"], messages=[dict(role="user",
            content=task + "\n\n<post>\n" + note["post"] + "\n</post>")]) for note in notes]
        references = [dict(note_id=note["note_id"], split=split, text=note["post"],
                           subjects=note["teacher"]) for note in notes]
        # Only the note_id headers of other splits may be inspected. Their
        # contents deliberately cannot be decoded as JSON or subject answers.
        train_ids = ["train-a"] + [f"train-{i}" for i in range(1, milestones[-1])]
        reference_lines = [json.dumps(dict(note_id=i))[:-1] + ', "poison": INVALID TRAIN CONTENT}'
                           for i in train_ids]
        if split == "evaluation":
            reference_lines.extend(json.dumps(row) for row in references)
            reference_lines.append('{"note_id":"test-a", "poison": INVALID RESERVED CONTENT}')
        else:
            reference_lines.append('{"note_id":"evaluation-a", "poison": INVALID VALIDATION CONTENT}')
            reference_lines.extend(json.dumps(row) for row in references)
        (prepared / "references.jsonl").write_text("\n".join(reference_lines) + "\n")
        (prepared / f"{split}.jsonl").write_text("\n".join(json.dumps(row) for row in evaluation) + "\n")
        manifest = dict(schema_version=2, tasks=dict(subjects="ASv6.100"),
            train_note_ids=train_ids,
            evaluation_note_ids=[note["note_id"] for note in notes] if split == "evaluation" else ["evaluation-a"],
            test_note_ids=[note["note_id"] for note in notes] if split == "test" else ["test-a"],
            subject_instruction_sha256=hashlib.sha256(task.encode()).hexdigest(),
            outputs={name: run.sha256(prepared / name) for name in (f"{split}.jsonl", "references.jsonl")})
        manifest["outputs"].update({name: "f" * 64 for name in ("train.jsonl",)
                                   + (("test.jsonl",) if split == "evaluation" else ("evaluation.jsonl",))})
        run.write_json(prepared / "manifest.json", manifest)
        model_outputs = []
        for index in range(models):
            output = root / f"model-{index}"
            config = dict(model=f"fixture/model-{index}", revision=str(index + 1) * 40,
                data=str(prepared), training_milestones=list(milestones), evaluation_tasks=["subjects"],
                max_new_tokens=dict(subjects=64), subject_batching=dict(budget_bytes=4096,
                    workspace_bytes=0, prefill_bytes_per_token=1, attention_matrix_count=4))
            run.write_json(output / "manifest.json", dict(config=config, dataset=manifest))
            plan = dict(note_ids=train_ids, milestones=list(milestones), examples_per_update=8)
            run.write_json(output / "training-plan.json", plan)
            run.seal_files(output, "provenance.complete.json", ["manifest.json", "training-plan.json"])
            for update, cursor in enumerate(milestones, 1):
                checkpoint = output / f"checkpoints/checkpoint-{cursor}"
                run.write_json(checkpoint / "training.json", dict(cursor=cursor, updates=update,
                    consumed_note_ids=train_ids[:cursor], manifest_sha256=run.sha256(output / "manifest.json"),
                    plan_sha256=run.sha256(output / "training-plan.json")))
                weight = checkpoint / "adapter_model.safetensors"
                weight.write_bytes(b"Fixture weight bytes: never needed by an offline review preview.")
                run.write_json(checkpoint / "complete.json", run.file_hashes(checkpoint))
                weight.write_bytes(b"Changed weight bytes prove the preview does not hash weights.")
            versions = ["baseline"] + [f"checkpoint-{m}" for m in
                                      (milestones if split == "evaluation" else (milestones[-1],))]
            for version in versions:
                stage = output / (version if version == "baseline" else "evaluations/" + version)
                if split == "test":
                    stage = output / "test" / version
                    checkpoint = None if version == "baseline" else output / "checkpoints" / version
                    run.write_json(stage / "test-collection.json", run.subject_test_source(output, checkpoint))
                self.stage(stage, evaluation, [note["answer"] for note in notes], split=split, config=config)
            if split == "evaluation":
                (output / "test").mkdir()
                (output / "test/poison").write_text("Reserved saved generations must not be read.")
            model_outputs.append(output)
        return prepared / "manifest.json", model_outputs

    def stage(self, directory, evaluation, answers, *, split="evaluation", config=None):
        batch = dict(indices=list(range(len(evaluation))), prompt_width=1, estimated_bytes=100)
        plan = dict(policy=config["subject_batching"] if split == "test" else {}, memory={}, max_new_tokens=64,
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
        self.assertEqual(run.subject_stage_summary(directory, {split: evaluation}, split=split)["notes"], len(evaluation))

    def test_explicit_test_preview_uses_only_baseline_and_final_checkpoint(self):
        notes = [dict(note_id=f"held-out-{i}", post=f"Held-out cable {i}.", teacher=TEACHER,
                      answer=answer(STUDENT)) for i in range(2)]
        manifest, outputs = self.fixture(notes, models=3, split="test", milestones=(1, 2))
        for output in outputs:
            (output / "test/checkpoint-1").mkdir()
            (output / "test/checkpoint-1/complete.json").write_text("INVALID INTERMEDIATE CHECKPOINT")
            (output / "baseline").mkdir()
            (output / "baseline/complete.json").write_text("INVALID VALIDATION OUTPUT")
        report = self.preview(manifest, outputs, split="test")
        self.assertEqual(report["dataset"]["split"], "test")
        self.assertEqual(report["totals"]["outputs"], 12)
        self.assertEqual(report["totals"]["versions"], 6)
        for model in report["models"]:
            self.assertEqual([v["version"] for v in model["versions"]], ["baseline", "checkpoint-2"])
        self.assertNotIn(str(manifest.parent / "evaluation.jsonl"), report["sources"])
        self.assertIn(str(manifest.parent / "test.jsonl"), report["sources"])

    def test_native_cli_test_preview_preserves_test_source_binding(self):
        manifest, outputs = self.fixture(split="test")
        path = self.root / "test-preview.json"
        self.native("preview-distillation-review", manifest, "--model-output", outputs[0],
                    "--split", "test", "--output", path)
        report = run.read_json(path)
        self.assertEqual(report["dataset"]["split"], "test")
        self.assertEqual(report["totals"]["outputs"], 2)

    def test_test_preview_rejects_resealed_wrong_checkpoint_collection(self):
        manifest, outputs = self.fixture(split="test")
        stage = outputs[0] / "test/checkpoint-1"
        source = run.read_json(stage / "test-collection.json")
        source["checkpoint"] = None
        run.write_json(stage / "test-collection.json", source)
        run.write_json(stage / "complete.json", run.file_hashes(stage))
        with self.assertRaisesRegex(ValueError, "test collection source"):
            self.preview(manifest, outputs, split="test")

    def preview(self, manifest, outputs, **options):
        from sse_multivector import distillation_review_preview
        return distillation_review_preview.preview(manifest, outputs, **options)

    def tokens(self, value):
        return len(tiktoken.get_encoding("o200k_base").encode(value, disallowed_special=()))

    def rendered_reviews(self, check, post, teacher, pairs):
        task = AS.read_text()
        directory = PROJECT / "sse_multivector/distillation-review-v1"
        filenames = dict(matching="matching-prompt-v3.md", support="support-prompt-v2.md",
                         relationship="relationship-prompt-v2.md")
        path = directory / filenames[check]
        template = path.read_text()
        catalog = []
        for row in teacher:
            if row["subject"] not in [entry["subject"] for entry in catalog]:
                catalog.append(dict(id=f"T{len(catalog) + 1:02d}", subject=row["subject"]))
        result = []
        for parent, subject in pairs:
            if check == "matching":
                variables = dict(POST=json.dumps(post, ensure_ascii=False),
                    MATCH_INPUT=json.dumps(dict(teacher_subjects=catalog, student_subject=subject), ensure_ascii=False))
            elif check == "support":
                end = "Derive broader headings by generalizing source meanings without adding restrictions."
                variables = dict(ASV6_100_SUPPORT_RULES=task[:task.index(end) + len(end)],
                    SUPPORT_INPUT=json.dumps(dict(post=post, student_subject=subject), ensure_ascii=False))
            else:
                start = "Judge each parent-child pair using only its `subject` strings across possible posts in any domain."
                end = "The post's domain, `context` and other entries cannot supply a missing heading restriction."
                variables = dict(ASV6_100_PARENT_CHILD_RULES=task[task.index(start):task.index(end) + len(end)],
                    RELATIONSHIP_INPUT=json.dumps(dict(parent_subject=parent, child_subject=subject), ensure_ascii=False))
            result.append(render(template, variables))
        return path, template, result

    def native(self, *args, environment=None):
        result = subprocess.run([sys.executable, str(LAUNCHER), "--project-root", str(PROJECT),
            *map(str, args)], cwd=PROJECT, env=environment,
            capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout

    def timing_experiment(self, check, *, name=None, defect=None, warmup=False):
        directory = self.root / (name or check + "-timing")
        directory.mkdir()
        log = directory / "calls.json"
        worker = directory / "fake-runner"
        fixture_worker = PROJECT.parent / "experiment-runner/tests/fixtures/fake-runner.py"
        worker.write_text(fixture_worker.read_text().replace('if prompt.startswith("GENERIC PROMPT"):',
            'if prompt.startswith(("DSMv3", "DSSv2", "DSLv2")):'))
        worker.chmod(0o755)
        prompts = PROJECT / "sse_multivector/distillation-review-v1"
        filenames = dict(matching="matching-prompt-v3.md", support="support-prompt-v2.md",
                         relationship="relationship-prompt-v2.md")
        prompt = prompts / filenames[check]
        if defect == "prompt":
            changed = directory / "changed-prompt.md"
            changed.write_text(prompt.read_text() + "\nChanged fixture prompt.\n")
            prompt = changed
        reference = prompts / "teacher-relative-source.json"
        bound = dict(path=str(reference), sha256=run.sha256(reference))
        if check == "matching":
            source = dict(schema_version=1, review_source=bound, cases=[dict(id="semantic", case="TC02",
                student_number="1.1.1.1", replacements=[], expected_teacher_number="1.1.1.1",
                expected_reason="Existing complete-meaning control.", partition="development")])
            adapter, prompt_id, schema_name = "distillation_matching", "DSMv3", "matching-response-schema.json"
            response = dict(teacher_id="T04", reason="Fixture complete-meaning response.")
        else:
            source = dict(schema_version=1, check=check, review_source=bound,
                cases=[dict(id="semantic", case="TC02" if check == "support" else "TC04",
                    student_number="1.1.1.1" if check == "support" else "1.1.1.2",
                    expected_reason="Existing authored control.")])
            adapter = "distillation_verdict"
            prompt_id = "DSSv2" if check == "support" else "DSLv2"
            schema_name = "boolean-response-schema.json"
            # Deliberately disagree with the support gold: valid receipts remain
            # timing observations even when a semantic answer is disputed.
            response = dict(valid=False, reason="Fixture semantic response.")
        prefix_arguments = []
        if warmup:
            self.assertEqual(check, "matching")
            post = 'A "quoted" cable label.\n' + "word " * 1100
            variables = dict(POST=json.dumps(post, ensure_ascii=False),
                MATCH_INPUT=json.dumps(dict(teacher_subjects=[dict(id="T04", subject="2 m cable A")],
                    student_subject="Cable A, two metres long"), ensure_ascii=False))
            source = dict(cases=[dict(id="semantic", inputs=variables)])
            adapter = "generic"
            text = render(prompt.read_text(), variables)
            prefix = text[:text.index('"student_subject": ') + len('"student_subject": ')]
            self.assertGreaterEqual(self.tokens(prefix), 1024)
            prefix_path = directory / "prefix.txt"
            prefix_path.write_text(prefix)
            prefix_arguments = ["--prompt-cache-prefix", prefix_path]
        schema = prompts / schema_name
        if defect == "schema":
            changed = directory / "changed-schema.json"
            run.write_json(changed, dict(json.loads(schema.read_text()), title="Changed fixture schema"))
            schema = changed
        source_path = directory / "source.json"
        run.write_json(source_path, source)
        spec = directory / "spec.json"
        run.write_json(spec, dict(schema_version=1, prompt=dict(id=prompt_id, path=str(prompt)),
            dataset=dict(adapter=adapter, path=str(source_path)),
            runner=dict(provider="openai-codex", auth_file=None, model="gpt-6.1-sol",
                reasoning_effort="xhigh", concurrency=4 if defect == "settings" else 8,
                transport="sse", runner_binary=str(worker), output_schema_path=str(schema))))
        experiment = directory / "saved"
        environment = dict(os.environ, FAKE_RUNNER_LOG=str(log),
            FAKE_RUNNER_PROMPT_RESPONSE=json.dumps(response),
            FAKE_RUNNER_RESULT_OVERRIDE=json.dumps(dict(usage=dict(input_tokens=100,
                cached_input_tokens=10, output_tokens=20, reasoning_output_tokens=5))))
        self.native("prepare", experiment, "--spec", spec, "--repeat", *prefix_arguments,
                    environment=environment)
        self.native("run", experiment, "--max-new-attempts", 2 if warmup else 1, environment=environment)
        report = json.loads(self.native("show", experiment, "--json", environment=environment))
        self.assertEqual(report["cases"][0]["status"], "valid")
        self.assertFalse(report["cases"][0]["reused"])
        self.assertEqual(len(json.loads(log.read_text())), 2 if warmup else 1)
        return experiment, log, report

    def check(self, totals, name, occurrences, mechanical, semantic, distinct, rules):
        self.assertEqual(totals["checks"][name], dict(occurrences=occurrences, mechanical=mechanical,
            semantic=semantic, distinct_semantic_inputs=distinct, mechanical_rules=rules))

    def test_native_command_help_exposes_offline_preview(self):
        result = subprocess.run([sys.executable, str(LAUNCHER), "--project-root", str(PROJECT),
            "preview-distillation-review", "--help"], cwd=PROJECT,
            capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("--model-output", result.stdout)
        self.assertIn("--output", result.stdout)
        self.assertIn("--estimate", result.stdout)
        self.assertIn("--timing-experiment", result.stdout)

    def test_native_cli_previews_multiple_models_without_changing_sources(self):
        manifest, outputs = self.fixture(models=2)
        before = run.file_hashes(manifest.parent.parent)
        report_path = self.root / "preview.json"
        command = [sys.executable, str(LAUNCHER), "--project-root", str(PROJECT), "preview-distillation-review", str(manifest)]
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

    def test_estimates_count_exact_approved_rendering_before_and_after_grouping(self):
        manifest, outputs = self.fixture(models=2)
        plain = self.preview(manifest, outputs)
        before = run.file_hashes(manifest.parent.parent)
        report = self.preview(manifest, outputs, estimate=True)
        self.assertEqual(report["totals"], plain["totals"])
        self.assertEqual(report["models"], plain["models"])
        self.assertEqual(before, run.file_hashes(manifest.parent.parent))
        estimates = report["estimates"]
        self.assertEqual(estimates["tokenizer"], "o200k_base")
        self.assertEqual(estimates["input_token_basis"],
            "Rendered prompt text only; excludes provider instructions, message framing and output-schema overhead.")
        self.assertEqual(estimates["settings"], dict(model="gpt-6.1-sol", reasoning="xhigh", concurrency=8))
        post = "Cable A is 2 m long and is not longer than cable B."
        comparison = "Cable A is longer than cable B"
        expected_pairs = dict(
            matching=[("", comparison), ("", comparison), ("", "New heading"),
                      ("", "New heading"), ("", "Cable A"), ("", "cables")],
            support=[("", comparison), ("", comparison), ("", "New heading"),
                     ("", "New heading"), ("", "Cable A"), ("", "cables")],
            relationship=[("Cables", comparison), ("Cables", comparison), ("Tools", "2 m cable A")])
        distinct_total = token_total = occurrence_total = 0
        ids = dict(matching="DSMv3", support="DSSv2", relationship="DSLv2")
        for check, pairs in expected_pairs.items():
            with self.subTest(check=check):
                path, template, texts = self.rendered_reviews(check, post, TEACHER, pairs)
                unique = set(texts)
                counts = [self.tokens(text) for text in unique]
                saved = estimates["checks"][check]
                self.assertEqual(saved["prompt"], dict(id=ids[check], path=str(path), sha256=run.sha256(path)))
                self.assertEqual(report["sources"][str(path)], run.sha256(path))
                self.assertEqual(saved["distinct_inputs"], len(unique))
                self.assertEqual(saved["rendered_input_tokens"], sum(counts))
                self.assertEqual(saved["min_rendered_input_tokens"], min(counts))
                self.assertEqual(saved["max_rendered_input_tokens"], max(counts))
                occurrence_tokens = 4 * sum(self.tokens(text) for text in texts)
                self.assertEqual(saved["occurrence_rendered_input_tokens"], occurrence_tokens)
                first = re.search(r"\{[A-Z][A-Z0-9_]*\}", template)
                prefix_tokens = self.tokens(template[:first.start()])
                self.assertEqual(saved["automatic_prefix"], dict(version="automatic-prefix-warmup-v1",
                    tokenizer="o200k_base", estimated_prefix_tokens=prefix_tokens,
                    minimum_prefix_tokens=1024, eligible=prefix_tokens >= 1024, boundary=first[0]))
                distinct_total += len(unique)
                token_total += sum(counts)
                occurrence_total += occurrence_tokens
        self.assertEqual(estimates["totals"]["distinct_inputs"], distinct_total)
        self.assertEqual(estimates["totals"]["rendered_input_tokens"], token_total)
        self.assertEqual(estimates["totals"]["occurrence_rendered_input_tokens"], occurrence_total)

    def test_natural_prefixes_include_escaped_reference_context_and_count_unique_uses(self):
        post = 'A "quoted" cable label.\n' + "word " * 1100
        parent = 'Parent "restriction".\n' + "broad " * 1100
        first, second = 'Custom "one"\nline', 'Custom "two"\nline'
        teacher = subjects(("1", parent), ("1.1", "2 m cable A"))
        student = subjects(("1", parent), ("1.1", first), ("1.2", second), ("1.3", first))
        manifest, outputs = self.fixture([dict(note_id="validation-a", post=post,
                                               teacher=teacher, answer=answer(student))], models=2)
        report = self.preview(manifest, outputs, estimate=True)
        estimates = report["estimates"]
        warmup_tokens = cached_tokens = cold_tokens = 0
        for check in ("matching", "support", "relationship"):
            with self.subTest(check=check):
                _, _, texts = self.rendered_reviews(check, post, teacher, [(parent, first), (parent, second)])
                field = "child_subject" if check == "relationship" else "student_subject"
                marker = '"' + field + '": '
                prefix = texts[0].rsplit(marker, 1)[0] + marker
                self.assertTrue(all(text.startswith(prefix) for text in texts))
                self.assertIn('\\"', prefix)
                self.assertIn('\\n', prefix)
                count = self.tokens(prefix)
                self.assertGreaterEqual(count, 1024)
                saved = estimates["checks"][check]
                self.assertEqual(saved["distinct_inputs"], 2)
                self.assertEqual(saved["natural_prefix"], dict(groups=1, repeated_groups=1,
                    eligible_groups=1, warmup_calls=1, warmup_input_tokens=count,
                    potential_cached_input_tokens=2 * count, cold_first_potential_cached_input_tokens=count))
                expected_occurrences = 4 * sum(self.tokens(text) for text in [texts[0], texts[1], texts[0]])
                self.assertEqual(saved["occurrence_rendered_input_tokens"], expected_occurrences)
                warmup_tokens += count
                cached_tokens += 2 * count
                cold_tokens += count
        self.assertEqual(estimates["totals"]["warmup_calls"], 3)
        self.assertEqual(estimates["totals"]["warmup_input_tokens"], warmup_tokens)
        self.assertEqual(estimates["totals"]["potential_cached_input_tokens"], cached_tokens)
        self.assertEqual(estimates["totals"]["cold_first_potential_cached_input_tokens"], cold_tokens)

    def test_long_prefix_with_one_distinct_input_has_no_warmup(self):
        post, parent, wording = "word " * 1100, "broad " * 1100, "A new cable wording"
        teacher = subjects(("1", parent), ("1.1", "2 m cable A"))
        student = subjects(("1", parent), ("1.1", wording), ("1.2", wording))
        manifest, outputs = self.fixture([dict(note_id="validation-a", post=post,
                                               teacher=teacher, answer=answer(student))])
        estimates = self.preview(manifest, outputs, estimate=True)["estimates"]
        for check in ("matching", "support", "relationship"):
            with self.subTest(check=check):
                self.assertEqual(estimates["checks"][check]["distinct_inputs"], 1)
                self.assertEqual(estimates["checks"][check]["natural_prefix"], dict(groups=1,
                    repeated_groups=0, eligible_groups=0, warmup_calls=0, warmup_input_tokens=0,
                    potential_cached_input_tokens=0, cold_first_potential_cached_input_tokens=0))

    def test_mechanical_empty_and_invalid_outputs_have_zero_estimated_review_tokens(self):
        teacher = subjects(("1", "Cables"))
        notes = [dict(note_id="valid", post="Cables.", teacher=teacher, answer=answer(teacher)),
                 dict(note_id="empty", post="Cables.", teacher=teacher, answer=answer([])),
                 dict(note_id="invalid", post="Cables.", teacher=teacher, answer=answer([], raw="not JSON"))]
        manifest, outputs = self.fixture(notes)
        estimates = self.preview(manifest, outputs, estimate=True)["estimates"]
        for check in ("matching", "support", "relationship"):
            with self.subTest(check=check):
                saved = estimates["checks"][check]
                for field in ("distinct_inputs", "rendered_input_tokens", "occurrence_rendered_input_tokens",
                              "min_rendered_input_tokens", "max_rendered_input_tokens"):
                    self.assertEqual(saved[field], 0)
                self.assertEqual(saved["natural_prefix"], dict(groups=0, repeated_groups=0,
                    eligible_groups=0, warmup_calls=0, warmup_input_tokens=0,
                    potential_cached_input_tokens=0, cold_first_potential_cached_input_tokens=0))

    def test_native_cli_estimates_are_offline_and_timing_requires_estimate(self):
        manifest, outputs = self.fixture()
        before = run.file_hashes(manifest.parent.parent)
        report_path = self.root / "estimate.json"
        command = [sys.executable, str(LAUNCHER), "--project-root", str(PROJECT), "preview-distillation-review",
                   str(manifest), "--model-output", str(outputs[0]), "--output", str(report_path)]
        result = subprocess.run([*command, "--estimate"], cwd=PROJECT,
            capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(report_path.read_text())
        self.assertEqual(report["inference_calls"], 0)
        self.assertIn("estimates", report)
        self.assertEqual(before, run.file_hashes(manifest.parent.parent))
        result = subprocess.run([*command[:-1], str(self.root / "timing.json"),
            "--timing-experiment", str(self.root / "missing-timing-experiment")], cwd=PROJECT,
            capture_output=True, text=True, timeout=30)
        self.assertNotEqual(result.returncode, 0)
        self.assertRegex(result.stderr, r"requires? --estimate")

    def test_native_fresh_timing_receipts_project_all_checks_without_double_counting_reasoning(self):
        manifest, outputs = self.fixture()
        experiments, seconds = [], {}
        for check in ("matching", "support", "relationship"):
            experiment, log, native_report = self.timing_experiment(check)
            experiments.append(experiment)
            receipt = json.loads((experiment / "run/results.jsonl").read_text())
            seconds[check] = receipt["elapsed_seconds"]
            self.assertGreater(seconds[check], 0)
            if check == "support":
                self.assertEqual(native_report["qualification"]["incorrect_verdicts"], ["semantic"])
        before = {str(path): run.file_hashes(path) for path in experiments}
        report_path = self.root / "native-timing-estimate.json"
        arguments = ["preview-distillation-review", manifest, "--model-output", outputs[0], "--estimate",
                     "--output", report_path]
        for experiment in experiments:
            arguments.extend(["--timing-experiment", experiment])
        self.native(*arguments)
        report = json.loads(report_path.read_text())
        self.assertEqual(report["inference_calls"], 0)
        timing = report["estimates"]["timing"]
        self.assertTrue(timing["complete"])
        for check in ("matching", "support", "relationship"):
            summary = timing["checks"][check]
            self.assertEqual(summary["samples"], 1)
            self.assertEqual(summary["elapsed_seconds"], dict.fromkeys(("mean", "median", "p90", "min", "max"), seconds[check]))
            self.assertEqual(summary["output_tokens"], dict.fromkeys(("mean", "median", "p90", "min", "max"), 20))
            self.assertEqual(summary["reasoning_tokens"], dict.fromkeys(("mean", "median", "p90", "min", "max"), 5))
        for metric in ("mean", "median", "p90"):
            self.assertAlmostEqual(timing["projections"][metric]["service_hours_at_concurrency_8"],
                (4 * seconds["matching"] + 4 * seconds["support"] + 2 * seconds["relationship"]) / (8 * 3600))
            self.assertEqual(timing["projections"][metric]["output_tokens"], 10 * 20)
        self.assertEqual([stratum["cache_hit_calls"] for stratum in timing["strata"]], [1, 1, 1])
        self.assertEqual(before, {str(path): run.file_hashes(path) for path in experiments})
        for experiment in experiments:
            self.assertIn(str(experiment / "run/results.jsonl"), report["sources"])
            self.assertEqual(len(json.loads((experiment.parent / "calls.json").read_text())), 1)

    def test_incomplete_timing_samples_leave_all_total_projections_unknown(self):
        manifest, outputs = self.fixture()
        experiment, log, _ = self.timing_experiment("matching")
        timing = self.preview(manifest, outputs, estimate=True, timing_experiments=[experiment])["estimates"]["timing"]
        self.assertFalse(timing["complete"])
        self.assertEqual(set(timing["checks"]), {"matching"})
        for metric in ("mean", "median", "p90"):
            self.assertEqual(timing["projections"][metric],
                dict(service_hours_at_concurrency_8=None, output_tokens=None))
        self.assertEqual(len(json.loads(log.read_text())), 1)

    def test_timing_rejects_changed_bindings_reuse_and_corrupt_native_receipts(self):
        manifest, outputs = self.fixture()
        for defect in ("prompt", "schema", "settings", "reuse", "receipt"):
            with self.subTest(defect=defect):
                experiment, log, _ = self.timing_experiment("support", name="bad-" + defect,
                    defect=defect if defect in ("prompt", "schema", "settings") else None)
                if defect == "reuse":
                    reused = experiment.parent / "reused"
                    self.native("prepare", reused, "--from", experiment)
                    self.native("run", reused)
                    reused_report = json.loads(self.native("show", reused, "--json"))
                    self.assertTrue(reused_report["cases"][0]["reused"])
                    experiment = reused
                elif defect == "receipt":
                    path = experiment / "run/results.jsonl"
                    receipt = json.loads(path.read_text())
                    receipt["model_result"]["prompt_sha256"] = "f" * 64
                    path.write_text(json.dumps(receipt) + "\n")
                from experiment_runner.extraction_pipeline import RunnerError
                with self.assertRaisesRegex((ValueError, RunnerError), "timing|receipt|prompt"):
                    self.preview(manifest, outputs, estimate=True, timing_experiments=[experiment])
                self.assertEqual(len(json.loads(log.read_text())), 1)

    def test_native_prefix_warmup_is_excluded_from_timing_observations(self):
        manifest, outputs = self.fixture()
        experiment, log, native_report = self.timing_experiment("matching", warmup=True)
        self.assertEqual(native_report["cache_warmup"]["attempts"], 1)
        self.assertEqual(native_report["cache_warmup"]["usage"]["output_tokens"], 20)
        records = [json.loads(line) for line in (experiment / "run/results.jsonl").read_text().splitlines()]
        self.assertEqual(len(records), 1)
        actual = next(record for record in records if record["job_key"] == "prompt:semantic")
        timing = self.preview(manifest, outputs, estimate=True, timing_experiments=[experiment])["estimates"]["timing"]
        self.assertEqual(timing["checks"]["matching"]["samples"], 1)
        self.assertEqual(timing["checks"]["matching"]["elapsed_seconds"]["mean"], actual["elapsed_seconds"])
        self.assertEqual(timing["checks"]["matching"]["output_tokens"]["mean"], 20)
        self.assertEqual(timing["strata"], [dict(experiment=str(experiment), check="matching", samples=1,
            prefix_role_format=True, cache_hit_calls=1, excluded_warmup_calls=1)])
        self.assertEqual(len(json.loads(log.read_text())), 2)


if __name__ == "__main__":
    unittest.main()
