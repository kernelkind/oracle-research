"""Complete saved-answer review preparation through the native runner."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from sse_multivector import test_distillation_review_preview as preview_fixtures

answer, subjects = preview_fixtures.answer, preview_fixtures.subjects


PROJECT = Path(__file__).resolve().parents[1]
LAUNCHER = PROJECT.parent / "experiment-runner/bin/experiment-runner"


class DistillationReviewEvaluationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def fixture(self, notes=None, *, name="fixture"):
        fixture = preview_fixtures.DistillationReviewPreviewTests()
        fixture.root = self.root
        return fixture.fixture(notes, name=name)

    def selection(self, notes=None, *, name="fixture", random_count=1):
        from sse_multivector.distillation_review_trial import prepare_trial
        manifest, outputs = self.fixture(notes, name=name)
        result = prepare_trial(manifest, outputs, self.root / ("selection-" + name), random_count=random_count, hard_count=0,
                               seed="native-evaluation-fixture")
        return Path(result["selection_path"])

    def worker(self):
        worker = self.root / "fake-runner"
        text = (PROJECT.parent / "experiment-runner/tests/fixtures/fake-runner.py").read_text()
        text = text.replace('if prompt.startswith("GENERIC PROMPT"):',
                            'if prompt.startswith(("DSMv3", "DSSv2", "DSLv2", "DSLv4")):')
        text = text.replace('if stage == "prompt":',
            'if stage == "prompt":\n'
            '    os.environ["FAKE_RUNNER_PROMPT_RESPONSE"] = json.dumps('
            '{"teacher_id": None, "reason": "Fixture unmatched wording."} if prompt.startswith("DSMv3") '
            'else {"valid": True, "reason": "Fixture semantic verdict."})')
        worker.write_text(text)
        worker.chmod(0o755)
        return worker

    def native(self, *args):
        result = subprocess.run([sys.executable, str(LAUNCHER), "--project-root", str(PROJECT),
            *map(str, args)], cwd=PROJECT,
            env=dict(os.environ, FAKE_RUNNER_LOG=str(self.root / "calls.json")),
            capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout

    def test_prepare_preserves_complete_occurrences_and_native_mechanics_without_calls(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        selected = self.selection()
        prepared = evaluation.prepare(selected, self.root / "evaluation", runner_binary=self.worker())
        cases = {name: [] for name in ("matching", "support", "relationship")}
        for entry in prepared["experiments"]:
            report = json.loads(self.native("show", entry["path"], "--json"))
            cases[entry["check"]].extend(report["cases"])
            self.assertEqual(report["settings"]["model"], "gpt-6.1-sol")
            self.assertEqual(report["settings"]["reasoning_effort"], "xhigh")
            self.assertEqual(report["settings"]["concurrency"], 30)
            self.assertEqual(report["settings"]["timeout_seconds"], 3600)
            spec = json.loads((self.root / "evaluation" / "specs" / (Path(entry["path"]).name + ".json")).read_text())
            self.assertNotIn("concurrency", spec["runner"])
        self.assertEqual({name: len(rows) for name, rows in cases.items()},
                         dict(matching=11, support=11, relationship=6))
        self.assertEqual(sum(case.get("origin") == "mechanical" for rows in cases.values() for case in rows), 13)
        self.assertTrue(all(case["evidence"]["expectation_status"] == "unresolved"
                            for rows in cases.values() for case in rows))
        self.assertEqual(json.loads(selected.read_text())["settings"]["concurrency"], 8)
        self.assertNotIn("answer_ids", prepared)
        self.assertFalse((self.root / "calls.json").exists())

    def test_native_cli_prepares_a_reasoning_override_without_changing_selection(self):
        selected = self.selection()
        frozen = selected.read_bytes()
        self.native("prepare-distillation-review-evaluation", selected,
            "--output", self.root / "high", "--runner-binary", self.worker(),
            "--reasoning-effort", "high")
        from sse_multivector import distillation_review_evaluation as evaluation
        report = evaluation.report(self.root / "high")
        self.assertTrue(all(row['settings']['reasoning_effort'] == 'high' for row in report['experiments']))
        self.assertEqual(selected.read_bytes(), frozen)
        self.assertFalse((self.root / 'calls.json').exists())

    def test_native_cli_prepares_high_matching_with_medium_other_checks(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        selected = self.selection()
        frozen = selected.read_bytes()
        baseline = self.root / "medium-default"
        evaluation.prepare(selected, baseline, reasoning_effort="medium")
        destination = self.root / "mixed-efforts"
        self.native("prepare-distillation-review-evaluation", selected,
            "--output", destination, "--reasoning-effort", "medium",
            "--matching-reasoning-effort", "high")
        original = evaluation.report(baseline)
        changed = evaluation.report(destination)
        for old, new in zip(original["experiments"], changed["experiments"]):
            check = new["cases"][0]["evidence"]["check"]
            self.assertEqual(new["settings"]["reasoning_effort"],
                             "high" if check == "matching" else "medium")
            self.assertEqual({k: v for k, v in new["settings"].items() if k != "reasoning_effort"},
                             {k: v for k, v in old["settings"].items() if k != "reasoning_effort"})
            self.assertEqual([(c["id"], c["inputs"], c["evidence"], c["prompt"], c.get("origin"))
                              for c in new["cases"]],
                             [(c["id"], c["inputs"], c["evidence"], c["prompt"], c.get("origin"))
                              for c in old["cases"]])
        self.assertEqual(selected.read_bytes(), frozen)
        self.assertFalse((self.root / "calls.json").exists())

    def test_bad_matching_effort_is_rejected_before_creating_output(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        destination = self.root / "invalid-effort"
        with self.assertRaisesRegex(ValueError, "matching_reasoning_effort"):
            evaluation.prepare(self.root / "missing-selection.json", destination,
                               matching_reasoning_effort="none")
        self.assertFalse(destination.exists())

    def test_native_cli_prepares_medium_support_with_high_other_checks(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        selected = self.selection()
        frozen = selected.read_bytes()
        baseline = self.root / "high-default"
        evaluation.prepare(selected, baseline, reasoning_effort="high")
        destination = self.root / "medium-support"
        self.native("prepare-distillation-review-evaluation", selected,
            "--output", destination, "--reasoning-effort", "high",
            "--support-reasoning-effort", "medium")
        original = evaluation.report(baseline)
        changed = evaluation.report(destination)
        self.assertEqual(len(changed["experiments"]), len(original["experiments"]))
        for old, new in zip(original["experiments"], changed["experiments"]):
            check = new["cases"][0]["evidence"]["check"]
            self.assertEqual(new["settings"]["reasoning_effort"],
                             "medium" if check == "support" else "high")
            self.assertEqual({k: v for k, v in new["settings"].items() if k != "reasoning_effort"},
                             {k: v for k, v in old["settings"].items() if k != "reasoning_effort"})
            self.assertEqual([(c["id"], c["inputs"], c["evidence"], c["prompt"], c.get("origin"))
                              for c in new["cases"]],
                             [(c["id"], c["inputs"], c["evidence"], c["prompt"], c.get("origin"))
                              for c in old["cases"]])
        self.assertEqual(selected.read_bytes(), frozen)
        self.assertFalse((self.root / "calls.json").exists())

    def test_bad_support_effort_is_rejected_before_creating_output(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        destination = self.root / "invalid-support-effort"
        with self.assertRaisesRegex(ValueError, "support_reasoning_effort"):
            evaluation.prepare(self.root / "missing-selection.json", destination,
                               support_reasoning_effort="none")
        self.assertFalse(destination.exists())

    def test_prepare_answer_subset_preserves_complete_native_cases_and_frozen_sources(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        from sse_multivector import distillation_review_assessment as assessment
        notes = [dict(note_id="validation-" + letter, post="Cable " + letter + ".",
            teacher=subjects(("1", "Cable " + letter)), answer=answer(subjects(
                ("1", "Cable " + letter), ("1.1", "Detail " + letter), ("2", "Other " + letter))))
            for letter in ("A", "B")]
        selected = self.selection(notes, random_count=2)
        frozen = selected.read_bytes()
        answers = json.loads(frozen)["random"]["answers"]
        identifier = answers[1]["id"]
        context = self.root / "assessment"
        for row in answers:
            assessment.record(selected, row["id"], context,
                teacher_meanings=[dict(teacher_numbers=["1"], required=True)],
                reason="Independent frozen fixture meaning.")
        snapshots = {path: path.read_bytes() for path in context.iterdir()}
        scoped = evaluation.prepare(selected, self.root / "scoped", runner_binary=self.worker(),
            assessment_directory=context, answer_ids=[identifier])
        self.assertEqual(scoped["answer_ids"], [identifier])
        baseline = self.root / "all"
        evaluation.prepare(selected, baseline, runner_binary=self.worker(), assessment_directory=context)
        complete = evaluation.report(baseline)
        changed = evaluation.report(self.root / "scoped")
        self.assertEqual([row["id"] for row in changed["random"]["answers"]], [identifier])
        self.assertEqual(changed["challenge"]["answers"], [])
        self.assertEqual(changed["summary"]["random"]["answers"], 1)
        old = next(row for row in complete["random"]["answers"] if row["id"] == identifier)
        for check in ("matching", "support", "relationship"):
            self.assertEqual([(c["id"], c["inputs"], c["evidence"], c["prompt"], c.get("origin"))
                              for c in changed["random"]["answers"][0]["checks"][check]],
                             [(c["id"], c["inputs"], c["evidence"], c["prompt"], c.get("origin"))
                              for c in old["checks"][check]])
        self.assertTrue(all(case["evidence"]["answer_id"] == identifier
                            for native in changed["experiments"] for case in native["cases"]))
        with self.assertRaisesRegex(ValueError, "answer_ids"):
            evaluation.run(self.root / "scoped", answer_ids=[answers[0]["id"]])
        self.assertEqual(selected.read_bytes(), frozen)
        self.assertEqual({path: path.read_bytes() for path in snapshots}, snapshots)
        self.assertFalse((self.root / "calls.json").exists())

    def test_unscoped_legacy_evaluation_versions_report_all_answers(self):
        from experiment_runner import experiment
        from sse_multivector import distillation_review_evaluation as evaluation
        notes = [dict(note_id="validation-" + letter, post="Cable " + letter + ".",
            teacher=subjects(("1", "Cable " + letter)), answer=answer(subjects(("1", "Cable " + letter))))
            for letter in ("A", "B")]
        selected = self.selection(notes, random_count=2)
        expected = [row["id"] for row in json.loads(selected.read_text())["random"]["answers"]]
        destination = self.root / "evaluation"
        evaluation.prepare(selected, destination, runner_binary=self.worker())
        path = destination / "evaluation.json"
        frozen = experiment.read(path)
        self.assertNotIn("answer_ids", frozen)
        for version in (1, 2):
            frozen["schema_version"] = version
            experiment.write(path, frozen)
            experiment.write(destination / "evaluation.complete.json",
                             {"evaluation.json": hashlib.sha256(path.read_bytes()).hexdigest()})
            result = evaluation.report(destination)
            self.assertEqual([row["id"] for row in result["random"]["answers"]], expected)
            self.assertEqual(result["summary"]["random"]["answers"], 2)
            self.assertEqual(result["summary"]["random"]["checks"]["matching"]["occurrences"], 2)
        self.assertFalse((self.root / "calls.json").exists())

    def test_native_cli_binds_relationship_prompt_override_without_changing_other_checks(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        selected = self.selection()
        frozen = selected.read_bytes()
        baseline = self.root / "default"
        evaluation.prepare(selected, baseline, runner_binary=self.worker())
        destination = self.root / "dslv4"
        prompt = PROJECT / "sse_multivector/distillation-review-v1/relationship-prompt-v4.md"
        self.native("prepare-distillation-review-evaluation", selected,
            "--output", destination, "--runner-binary", self.worker(),
            "--relationship-prompt", prompt, "--relationship-prompt-id", "DSLv4")
        original = evaluation.report(baseline)
        changed = evaluation.report(destination)
        for old, new in zip(original["experiments"], changed["experiments"]):
            check = new["cases"][0]["evidence"]["check"]
            self.assertEqual(new["prompt_id"], "DSLv4" if check == "relationship" else old["prompt_id"])
            self.assertEqual(new["settings"], old["settings"])
            self.assertEqual([(c["id"], c["inputs"], c["evidence"], c.get("origin")) for c in new["cases"]],
                             [(c["id"], c["inputs"], c["evidence"], c.get("origin")) for c in old["cases"]])
            if check == "relationship":
                self.assertTrue(all(c["prompt"].startswith("DSLv4") for c in new["cases"]))
            else:
                self.assertEqual([c["prompt"] for c in new["cases"]], [c["prompt"] for c in old["cases"]])
        self.assertEqual(evaluation._DEFINITIONS["relationship"][0], "DSLv2")
        self.assertEqual(selected.read_bytes(), frozen)
        self.assertFalse((self.root / "calls.json").exists())

    def test_native_cli_prepares_repeated_answer_ids_without_changing_selection(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        notes = [dict(note_id="validation-" + letter, post="Cable " + letter + ".",
            teacher=subjects(("1", "Cable " + letter)),
            answer=answer(subjects(("1", "Cable " + letter), ("1.1", "Detail " + letter))))
            for letter in ("A", "B", "C")]
        selected = self.selection(notes, random_count=3)
        frozen = selected.read_bytes()
        answers = json.loads(frozen)["random"]["answers"]
        identifiers = [answers[2]["id"], answers[0]["id"]]
        destination = self.root / "subset"
        self.native("prepare-distillation-review-evaluation", selected,
            "--output", destination, "--runner-binary", self.worker(),
            "--answer-id", identifiers[0], "--answer-id", identifiers[1])
        report = evaluation.report(destination)
        self.assertEqual(json.loads((destination / "evaluation.json").read_text())["answer_ids"], identifiers)
        self.assertEqual([row["id"] for row in report["random"]["answers"]],
                         [answers[0]["id"], answers[2]["id"]])
        self.assertTrue(all(case["evidence"]["answer_id"] in identifiers
                            for native in report["experiments"] for case in native["cases"]))
        self.assertTrue(all(row["settings"]["reasoning_effort"] == "xhigh" for row in report["experiments"]))
        self.assertNotIn("--concurrency", self.native("prepare-distillation-review-evaluation", "--help"))
        self.assertEqual(selected.read_bytes(), frozen)
        self.assertFalse((self.root / "calls.json").exists())

    def test_prepare_relationship_history_override_preserves_other_checks_and_fallback(self):
        from experiment_runner import experiment
        from sse_multivector import distillation_review_evaluation as evaluation
        selected = self.selection()
        frozen = selected.read_bytes()
        relationship_history = self.root / "relationship-history"
        relationship_history.mkdir()
        changed = evaluation.prepare(selected, self.root / "override", runner_binary=self.worker(),
            history_root=self.root, relationship_history_root=relationship_history)
        for entry in changed["experiments"]:
            _, _, manifest = experiment.load(Path(entry["path"]))
            expected = relationship_history if entry["check"] == "relationship" else self.root
            self.assertEqual(manifest["request_reuse"]["history_root"], str(expected))
        cli_override = self.root / "cli-override"
        self.native("prepare-distillation-review-evaluation", selected,
            "--output", cli_override, "--runner-binary", self.worker(), "--history-root", self.root,
            "--relationship-history-root", relationship_history)
        for entry in evaluation.report(cli_override)["experiments"]:
            _, _, manifest = experiment.load(Path(entry["experiment"]))
            check = entry["cases"][0]["evidence"]["check"]
            self.assertEqual(manifest["request_reuse"]["history_root"],
                             str(relationship_history if check == "relationship" else self.root))
        fallback = self.root / "fallback"
        self.native("prepare-distillation-review-evaluation", selected,
            "--output", fallback, "--runner-binary", self.worker(), "--history-root", self.root)
        for entry in evaluation.report(fallback)["experiments"]:
            _, _, manifest = experiment.load(Path(entry["experiment"]))
            self.assertEqual(manifest["request_reuse"]["history_root"], str(self.root))
        self.assertEqual(selected.read_bytes(), frozen)
        self.assertFalse((self.root / "calls.json").exists())

    def test_native_cli_v7_supplies_post_to_actual_edges_and_coverage_compatibility(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        from sse_multivector import distillation_review_assessment as assessment
        teacher = subjects(("1", "Cables"), ("1.1", "2 m cable A"))
        student = subjects(("1", "Length measurements"), ("1.1", "Cable A, two metres long"))
        post = "Cable A is 2 m long."
        selected = self.selection([dict(note_id="validation-a", post=post,
                                        teacher=teacher, answer=answer(student))])
        frozen = selected.read_bytes()
        context = self.root / "assessment"
        assessment.record(selected, "R01", context, teacher_meanings=[
            dict(teacher_numbers=["1"], required=False), dict(teacher_numbers=["1.1"], required=True)],
            reason="Complete two-metre cable wording is required.")
        destination = self.root / "dslv7"
        prompt = PROJECT / "sse_multivector/distillation-review-v1/relationship-prompt-v7.md"
        source = self.root / "source.json"
        source.write_text(json.dumps(dict(schema_version=1, check="relationship",
            selection=dict(path=str(selected), sha256=hashlib.sha256(frozen).hexdigest()),
            assessment_directory=str(context))))
        spec = self.root / "spec.json"
        spec.write_text(json.dumps(dict(schema_version=1, prompt=dict(id="DSLv7", path=str(prompt)),
            dataset=dict(adapter="distillation_review_evaluation", path=str(source)),
            runner=dict(provider="openai-codex", auth_file=None, model="gpt-6.1-sol",
                reasoning_effort="xhigh", runner_binary=str(self.worker()),
                output_schema_path=str(prompt.parent / "boolean-response-schema.json")))))
        self.native("prepare", destination, "--spec", spec)
        relationships = json.loads(self.native("show", destination, "--json"))["cases"]
        self.assertEqual([case["evidence"]["role"] for case in relationships],
                         ["actual_relationship", "compatibility", "compatibility"])
        for case in relationships:
            self.assertEqual(case["inputs"]["POST"], post)
            self.assertIn("<post>\n" + post + "\n</post>", case["prompt"])
            self.assertTrue(case["prompt"].startswith("DSLv7"))
        pairs = [json.loads(case["inputs"]["RELATIONSHIP_INPUT"]) for case in relationships]
        self.assertEqual(pairs, [dict(parent_subject="Length measurements", child_subject="Cable A, two metres long"),
                                dict(parent_subject="Length measurements", child_subject="2 m cable A"),
                                dict(parent_subject="Cable A, two metres long", child_subject="2 m cable A")])
        self.assertEqual(evaluation._DEFINITIONS["relationship"][0], "DSLv2")
        self.assertEqual(selected.read_bytes(), frozen)
        self.assertFalse((self.root / "calls.json").exists())

    def test_native_v9_contexts_follow_the_bound_coverage_occurrence_and_preserve_unknown_pairs(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        from sse_multivector import distillation_review_assessment as assessment
        child = "MILFs as a tag for Example Film"
        teacher = [dict(number="10", subject="Tags", context="Category tags."),
            dict(number="10.1", subject=child, context="#milf is a category attached to Example Film."),
            dict(number="6", subject="Mothers", context="#moms names mothers."),
            dict(number="9", subject="MILFs",
                 context="#milf denotes the sexual category of sexually desirable mothers."),
            dict(number="9.1", subject=child, context="#milf is a category attached to Example Film.")]
        student = subjects(("1", "Mothers"), ("1.1", child),
                           ("2", "Film reviews"), ("2.1", "Positive film reviews"))
        selected = self.selection([dict(note_id="validation-a", post="Example Film #moms #milf",
                                        teacher=teacher, answer=answer(student))])
        frozen = selected.read_bytes()
        context = self.root / "assessment"
        assessment.record(selected, "R01", context, teacher_meanings=[
            dict(teacher_numbers=["10"], required=False), dict(teacher_numbers=["6"], required=False),
            dict(teacher_numbers=["9"], required=False),
            dict(teacher_numbers=["9.1", "10.1"], required=True)], reason="Frozen fixture meaning groups.")
        prompt = PROJECT / "sse_multivector/distillation-review-v1/relationship-prompt-v9.md"
        source = self.root / "source.json"
        source.write_text(json.dumps(dict(schema_version=1, check="relationship",
            selection=dict(path=str(selected), sha256=hashlib.sha256(frozen).hexdigest()),
            assessment_directory=str(context))))
        spec = self.root / "spec.json"
        spec.write_text(json.dumps(dict(schema_version=1, prompt=dict(id="DSLv9", path=str(prompt)),
            dataset=dict(adapter="distillation_review_evaluation", path=str(source)),
            runner=dict(provider="openai-codex", auth_file=None, model="gpt-6.1-sol", reasoning_effort="xhigh",
                runner_binary=str(self.worker()), output_schema_path=str(prompt.parent / "boolean-response-schema.json")))))
        self.native("prepare", self.root / "dslv9", "--spec", spec)
        rows = json.loads(self.native("show", self.root / "dslv9", "--json"))["cases"]
        placement = next(row for row in rows if row["evidence"]["role"] == "compatibility"
                         and row["evidence"]["heading_number"] == "1")
        self.assertEqual(placement["evidence"]["teacher_representative_number"], "9.1")
        self.assertEqual(placement["evidence"]["teacher_context_numbers"], ["6", "9", "9.1"])
        self.assertEqual(json.loads(placement["inputs"]["TEACHER_CONTEXTS"]),
                         [{key: row[key] for key in ("subject", "context")} for row in teacher[2:]])
        self.assertEqual(json.loads(placement["inputs"]["RELATIONSHIP_INPUT"]),
                         dict(parent_subject="Mothers", child_subject=child))
        self.assertNotEqual(placement.get("origin"), "mechanical")
        unknown = next(row for row in rows if row["evidence"]["role"] == "actual_relationship"
                       and row["evidence"]["student_number"] == "2.1")
        self.assertEqual(json.loads(unknown["inputs"]["TEACHER_CONTEXTS"]), [])
        self.assertEqual(json.loads(unknown["inputs"]["RELATIONSHIP_INPUT"]),
                         dict(parent_subject="Film reviews", child_subject="Positive film reviews"))
        for row in rows:
            self.assertNotIn("expected_valid", row["prompt"])
            self.assertNotIn("Frozen fixture meaning groups.", row["prompt"])
            self.assertTrue(row["prompt"].startswith("DSLv9"))
        self.assertEqual(evaluation._DEFINITIONS["relationship"][0], "DSLv2")
        self.assertEqual(selected.read_bytes(), frozen)
        self.assertFalse((self.root / "calls.json").exists())

    def test_prepare_answer_subset_rejects_invalid_ids_before_creating_output(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        selected = self.selection()
        identifier = json.loads(selected.read_text())["random"]["answers"][0]["id"]
        for index, value in enumerate(([], ["missing"], [identifier, identifier], "not-an-array", [""], [True])):
            destination = self.root / ("invalid-subset-" + str(index))
            with self.assertRaisesRegex(ValueError, "answer_ids"):
                evaluation.prepare(selected, destination, answer_ids=value)
            self.assertFalse(destination.exists())
        self.assertFalse((self.root / "calls.json").exists())

    def test_relationship_override_reuses_other_checks_and_runs_only_selected_answer(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        from sse_multivector import distillation_review_assessment as assessment
        notes = [dict(note_id="validation-" + letter, post="Cable " + letter + ".",
            teacher=subjects(("1", "Cable " + letter)), answer=answer(subjects(
                ("1", "Cable " + letter), ("1.1", "Detail " + letter), ("2", "Other " + letter))))
            for letter in ("A", "B")]
        selected = self.selection(notes, random_count=2)
        frozen = selected.read_bytes()
        answers = json.loads(frozen)["random"]["answers"]
        context = self.root / "assessment"
        for row in answers:
            assessment.record(selected, row["id"], context,
                teacher_meanings=[dict(teacher_numbers=["1"], required=True)],
                reason="Independent complete fixture source meaning.")
        worker = self.worker()
        baseline, changed = self.root / "default", self.root / "dslv4"
        evaluation.prepare(selected, baseline, runner_binary=worker, history_root=self.root,
                           assessment_directory=context)
        with patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.root / "calls.json")):
            evaluation.run(baseline)
        snapshots = {path: path.read_bytes() for path in baseline.rglob("*") if path.is_file()}
        calls = (self.root / "calls.json").read_bytes()
        prompt = PROJECT / "sse_multivector/distillation-review-v1/relationship-prompt-v4.md"
        relationship_worker = self.root / "relationship-runner"
        relationship_worker.write_text(worker.read_text() + "\n# A separately bound relationship worker.\n")
        relationship_worker.chmod(0o755)
        self.native("prepare-distillation-review-evaluation", selected, "--output", changed,
            "--runner-binary", worker, "--history-root", self.root, "--assessments", context,
            "--relationship-prompt", prompt, "--relationship-prompt-id", "DSLv4",
            "--relationship-runner-binary", relationship_worker)
        identifier = answers[0]["id"]
        self.native("run-distillation-review-evaluation", changed, "--answer-id", identifier,
                    "--max-new-attempts", 0)
        joined = evaluation.report(changed)
        self.assertEqual((self.root / "calls.json").read_bytes(), calls)
        first = joined["random"]["answers"][0]
        self.assertTrue(all(case["status"] == "valid" for check in ("matching", "support")
                            for case in first["checks"][check]))
        self.assertEqual(sum(case["status"] == "unrun" for case in first["checks"]["relationship"]), 3)
        self.native("run-distillation-review-evaluation", changed, "--answer-id", identifier,
                    "--max-new-attempts", 3)
        complete = evaluation.report(changed)
        self.assertEqual([row["status"] for row in complete["random"]["answers"]], ["complete", "pending"])
        for native in complete["experiments"]:
            plan = json.loads((Path(native["experiment"]) / "experiment.json").read_text())["plan"]
            check = native["cases"][0]["evidence"]["check"]
            expected_worker = relationship_worker if check == "relationship" else worker
            self.assertEqual(plan["runner"]["runner_binary"], str(expected_worker))
        self.assertEqual(len(json.loads((self.root / "calls.json").read_bytes())) - len(json.loads(calls)), 2)
        self.assertTrue(all(case["status"] == "unrun" for cases in complete["random"]["answers"][1]["checks"].values()
                            for case in cases if case.get("origin") != "mechanical"))
        self.assertEqual(selected.read_bytes(), frozen)
        self.assertEqual({path: path.read_bytes() for path in snapshots}, snapshots)

    def test_relationship_override_requires_both_flags_before_creating_output(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        selected = self.selection()
        prompt = PROJECT / "sse_multivector/distillation-review-v1/relationship-prompt-v4.md"
        for index, options in enumerate((dict(relationship_prompt=prompt),
                                        dict(relationship_prompt_id="DSLv4"))):
            destination = self.root / ("invalid-override-" + str(index))
            with self.assertRaisesRegex(ValueError, "must be supplied together"):
                evaluation.prepare(selected, destination, **options)
            self.assertFalse(destination.exists())
        self.assertFalse((self.root / "calls.json").exists())

    def test_reasoning_trials_bind_new_identities_and_preserve_baseline_artifacts(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        teacher = subjects(("1", "Cable A"))
        selected = self.selection([dict(note_id="validation-a", post="Cable A.", teacher=teacher,
            answer=answer(subjects(("1", "Different wording"))))])
        worker = self.worker()
        frozen = selected.read_bytes()
        baseline = self.root / "xhigh"
        evaluation.prepare(selected, baseline, runner_binary=worker, history_root=self.root)
        with patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.root / "calls.json")):
            first = evaluation.run(baseline)
            snapshots = {path: path.read_bytes() for path in baseline.rglob("*") if path.is_file()}
            for effort in ("high", "medium", "low"):
                destination = self.root / effort
                prepared = evaluation.prepare(selected, destination, runner_binary=worker,
                    history_root=self.root, reasoning_effort=effort)
                self.assertEqual(prepared["summary"]["requests"]["totals"]["new"], 2)
                report = evaluation.run(destination)
                self.assertTrue(all(row["settings"]["reasoning_effort"] == effort for row in report["experiments"]))
                for native, original in zip(report["experiments"], first["experiments"]):
                    self.assertEqual(native["prompt_id"], original["prompt_id"])
                    self.assertEqual([(case["input_sha256"], case["prompt"]) for case in native["cases"]],
                                     [(case["input_sha256"], case["prompt"]) for case in original["cases"]])
                    for setting in ("provider", "model", "transport", "concurrency", "timeout_seconds", "output_schema"):
                        self.assertEqual(native["settings"][setting], original["settings"][setting])
                self.assertEqual(report["generation_usage"]["original_calls"], 2)
        self.assertEqual(len(json.loads((self.root / "calls.json").read_text())), 8)
        self.assertEqual(selected.read_bytes(), frozen)
        self.assertEqual({path: path.read_bytes() for path in snapshots}, snapshots)
        self.assertEqual(evaluation.report(baseline)["generation_usage"]["original_calls"], 2)
        with self.assertRaisesRegex(ValueError, "reasoning_effort"):
            evaluation.prepare(selected, self.root / "invalid-effort", reasoning_effort="invalid")
        self.assertFalse((self.root / "invalid-effort").exists())

    def test_native_answer_subset_then_nested_expansion_retains_full_report(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        from sse_multivector import distillation_review_assessment as assessment
        notes = [dict(note_id="validation-" + letter, post="Cable " + letter + ". " + "word " * 1100,
            teacher=subjects(("1", "Cable " + letter)), answer=answer(subjects(
                ("1", "Heading " + letter + " broad" * 1100), ("1.1", "Detail " + letter), ("2", "Cable " + letter))))
            for letter in ("A", "B")]
        selected = self.selection(notes, random_count=2)
        bundle = json.loads(selected.read_text())
        answers = bundle["random"]["answers"]
        self.assertEqual(len({row["note_id"] for row in answers}), 2)
        context = self.root / "assessment"
        for row in answers:
            assessment.record(selected, row["id"], context,
                teacher_meanings=[dict(teacher_numbers=["1"], required=True)],
                reason="Independent complete fixture source meaning.")
        destination = self.root / "evaluation"
        evaluation.prepare(selected, destination, runner_binary=self.worker(), assessment_directory=context)
        self.native("run-distillation-review-evaluation", destination, "--answer-id", answers[0]["id"])
        first = evaluation.report(destination)
        first_answer, unselected = first["random"]["answers"]
        self.assertEqual(first_answer["status"], "complete")
        self.assertIn("scores", first_answer)
        self.assertEqual(unselected["status"], "pending")
        self.assertNotIn("scores", unselected)
        self.assertTrue(all(row["status"] == "unrun" for rows in unselected["checks"].values()
                            for row in rows if row.get("origin") != "mechanical"))
        self.assertEqual(sum(native.get("cache_warmup", {}).get("attempts", 0)
                             for native in first["experiments"]), 3)
        for native in first["experiments"]:
            if all(row["evidence"]["answer_id"] == answers[1]["id"] for row in native["cases"]):
                self.assertEqual(native.get("cache_warmup", {}).get("attempts", 0), 0)
        calls_before = len(json.loads((self.root / "calls.json").read_text()))
        first_receipts = [row.get("receipt") for rows in first_answer["checks"].values() for row in rows]
        with patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.root / "calls.json")):
            complete = evaluation.run(destination, answer_ids=[row["id"] for row in answers])
        self.assertEqual([row["status"] for row in complete["random"]["answers"]], ["complete", "complete"])
        self.assertEqual(sum(native.get("cache_warmup", {}).get("attempts", 0)
                             for native in complete["experiments"]), 6)
        self.assertEqual(len(json.loads((self.root / "calls.json").read_text())), calls_before * 2)
        self.assertEqual([row.get("receipt") for rows in complete["random"]["answers"][0]["checks"].values()
                          for row in rows], first_receipts)
        for native in first["experiments"]:
            if not any(row["evidence"]["answer_id"] == answers[0]["id"] and row.get("origin") != "mechanical"
                       for row in native["cases"]):
                continue
            settings = Path(native["experiment"]) / "execution-settings.jsonl"
            if not settings.exists():
                continue
            entries = [json.loads(line) for line in settings.read_text().splitlines()]
            for entry in entries[:1]:
                ids = entry["only"]
                self.assertTrue(all(identifier.startswith(answers[0]["id"] + ":") for identifier in ids))

    def test_answer_subset_validation_and_empty_selection_dispatch_nothing(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        destination = self.root / "evaluation"
        evaluation.prepare(self.selection(), destination, runner_binary=self.worker())
        identifier = evaluation.report(destination)["random"]["answers"][0]["id"]
        for invalid in (["missing"], [identifier, identifier], "not-an-array"):
            with self.assertRaisesRegex(ValueError, "answer_ids"):
                evaluation.run(destination, answer_ids=invalid)
        empty = evaluation.run(destination, answer_ids=[])
        self.assertEqual(empty["random"]["answers"][0]["status"], "pending")
        self.assertEqual(empty["generation_usage"]["original_calls"], 0)
        self.assertFalse((self.root / "calls.json").exists())

    def test_zero_allowance_reuses_only_selected_answer_in_every_check(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        from sse_multivector import distillation_review_assessment as assessment
        notes = [dict(note_id="validation-" + letter, post="Cable " + letter + ".",
            teacher=subjects(("1", "Cable " + letter)), answer=answer(subjects(
                ("1", "Cable " + letter), ("2", "Other " + letter)))) for letter in ("A", "B")]
        selected = self.selection(notes, random_count=2)
        answers = json.loads(selected.read_text())["random"]["answers"]
        context = self.root / "assessment"
        for row in answers:
            assessment.record(selected, row["id"], context,
                teacher_meanings=[dict(teacher_numbers=["1"], required=True)],
                reason="Independent complete fixture source meaning.")
        worker = self.worker()
        first, second = self.root / "first", self.root / "second"
        evaluation.prepare(selected, first, runner_binary=worker, history_root=self.root,
                           assessment_directory=context)
        with patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.root / "calls.json")):
            evaluation.run(first)
            calls = (self.root / "calls.json").read_bytes()
            evaluation.prepare(selected, second, runner_binary=worker, history_root=self.root,
                               assessment_directory=context)
            report = evaluation.run(second, max_new_attempts=0, answer_ids=[answers[0]["id"]])
        self.assertEqual((self.root / "calls.json").read_bytes(), calls)
        self.assertEqual([row["status"] for row in report["random"]["answers"]], ["complete", "pending"])
        self.assertTrue(all(row["status"] == "unrun" for rows in report["random"]["answers"][1]["checks"].values()
                            for row in rows if row.get("origin") != "mechanical"))

    def test_preparation_summary_counts_native_distinct_requests_and_remaining_work(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        prepared = evaluation.prepare(self.selection(), self.root / "evaluation", runner_binary=self.worker())
        requests = prepared["summary"]["requests"]
        self.assertEqual({name: row["distinct"] for name, row in requests["checks"].items()},
                         dict(matching=4, support=4, relationship=2))
        self.assertEqual(requests["totals"], dict(distinct=10, remaining=10, reusable=0, new=10,
                                                warmups_remaining=0))
        with patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.root / "calls.json")):
            complete = evaluation.run(self.root / "evaluation", max_new_attempts=10)
        self.assertEqual(complete["summary"]["requests"]["totals"],
                         dict(distinct=10, remaining=0, reusable=0, new=0, warmups_remaining=0))

    def test_native_run_dispatches_identical_inputs_once_and_joins_all_occurrences(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        prepared = evaluation.prepare(self.selection(), self.root / "evaluation", runner_binary=self.worker())
        for entry in prepared["experiments"]:
            self.assertFalse(entry["prefix_cached"])
            self.native("run", entry["path"], "--max-new-attempts", 10)
        report = evaluation.report(self.root / "evaluation")
        selected = report["random"]["answers"][0]
        self.assertEqual(selected["status"], "complete")
        self.assertEqual(selected["coverage"]["status"], "pending")
        self.assertEqual({check: len(rows) for check, rows in selected["checks"].items()},
                         dict(matching=11, support=11, relationship=6))
        self.assertEqual(len(json.loads((self.root / "calls.json").read_text())), 10)
        all_cases = [case for rows in selected["checks"].values() for case in rows]
        self.assertEqual(sum(case.get("reused", False) for case in all_cases), 5)
        self.assertEqual(sum(case.get("origin") == "mechanical" for case in all_cases), 13)
        repeated = [case for case in selected["checks"]["support"]
                    if case["evidence"]["student_number"] in ("1.3", "1.4")]
        self.assertEqual([case["parsed"] for case in repeated], [repeated[0]["parsed"]] * 2)
        self.assertEqual(report["generation_usage"]["original_calls"], 10)
        self.assertEqual(report["generation_usage"]["input_tokens"], 1000)
        self.assertEqual(report["generation_usage"]["output_tokens"], 200)
        self.assertEqual(report["generation_usage"]["reasoning_tokens"], 50)

    def test_only_long_repeated_natural_prefixes_get_native_warmups(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        post, parent = 'A "quoted" note.\n' + "word " * 1100, "Broad " * 1100
        teacher = subjects(("1", parent), ("1.1", "2 m cable A"))
        student = subjects(("1", parent), ("1.1", "First new wording"),
                           ("1.2", "Second new wording"), ("1.3", "First new wording"))
        prepared = evaluation.prepare(self.selection([dict(note_id="validation-a", post=post,
            teacher=teacher, answer=answer(student))]), self.root / "evaluation", runner_binary=self.worker())
        cached = [entry for entry in prepared["experiments"] if entry["prefix_cached"]]
        self.assertEqual({entry["check"] for entry in cached}, {"matching", "support", "relationship"})
        self.assertEqual(prepared["summary"]["requests"]["totals"],
                         dict(distinct=6, remaining=6, reusable=0, new=6, warmups_remaining=3))
        budget = self.root / "budget.json"
        budget.write_text(json.dumps(dict(schema_version=1, limit=9, used=0)))
        with patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.root / "calls.json")):
            report = evaluation.run(self.root / "evaluation", max_new_attempts=9, attempt_budget_path=budget)
        self.assertEqual(report["random"]["answers"][0]["status"], "complete")
        self.assertEqual(len(json.loads((self.root / "calls.json").read_text())), 9)
        self.assertEqual(json.loads(budget.read_text())["used"], 9)
        self.assertEqual(sum(native.get("cache_warmup", {}).get("attempts", 0)
                             for native in report["experiments"]), 3)
        for native in report["experiments"]:
            if native.get("cache_warmup", {}).get("attempts", 0):
                self.assertEqual(native["summary"]["reused"], 1)
                self.assertEqual(native["generation_usage"]["original_calls"], 3)

    def test_context_compatibility_uses_native_relationship_mechanics_and_complete_coverage(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        from sse_multivector import distillation_review_assessment as assessment
        teacher = subjects(("1", "Cables"), ("1.1", "2 m cable A"))
        selected = self.selection([dict(note_id="validation-a", post="Cable A is 2 m long.",
                                        teacher=teacher, answer=answer(teacher))])
        context = self.root / "assessment"
        assessment.record(selected, "R01", context, teacher_meanings=[
            dict(teacher_numbers=["1"], required=False), dict(teacher_numbers=["1.1"], required=True)],
            reason="Frozen independent fixture teacher meanings.")
        prepared = evaluation.prepare(selected, self.root / "evaluation", runner_binary=self.worker(),
                                      assessment_directory=context)
        for entry in prepared["experiments"]:
            self.native("run", entry["path"], "--max-new-attempts", 1)
        report = evaluation.report(self.root / "evaluation")
        result = report["random"]["answers"][0]
        relationships = result["checks"]["relationship"]
        self.assertEqual(len(relationships), 3)
        self.assertEqual(sum(case["evidence"]["role"] == "actual_relationship" for case in relationships), 1)
        self.assertEqual(sum(case["evidence"]["role"] == "compatibility" for case in relationships), 2)
        self.assertTrue(all(case["origin"] == "mechanical" for rows in result["checks"].values() for case in rows))
        self.assertEqual(result["coverage"]["status"], "complete")
        self.assertEqual(result["scores"]["coverage"]["value"], 1)
        self.assertEqual(result["scores"]["correctness"]["value"], 1)
        self.assertFalse((self.root / "calls.json").exists())

    def test_shared_native_execution_cap_and_budget_cover_every_group_and_resume(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        prepared = evaluation.prepare(self.selection(), self.root / "evaluation", runner_binary=self.worker())
        budget = self.root / "budget.json"
        budget.write_text(json.dumps(dict(schema_version=1, limit=10, used=0)))
        with patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.root / "calls.json")):
            partial = evaluation.run(self.root / "evaluation", max_new_attempts=3, attempt_budget_path=budget)
            self.assertEqual(len(json.loads((self.root / "calls.json").read_text())), 3)
            self.assertEqual(json.loads(budget.read_text())["used"], 3)
            self.assertEqual(partial["random"]["answers"][0]["status"], "pending")
            complete = evaluation.run(self.root / "evaluation", max_new_attempts=20, attempt_budget_path=budget)
        self.assertEqual(complete["random"]["answers"][0]["status"], "complete")
        self.assertEqual(json.loads(budget.read_text())["used"], 10)
        self.assertEqual(len(json.loads((self.root / "calls.json").read_text())), 10)

    def test_missing_match_under_compatible_heading_fails_existing_coverage_rule(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        from sse_multivector import distillation_review_assessment as assessment
        teacher = subjects(("1", "Cables"), ("1.1", "2 m cable A"), ("2", "Tools"))
        student = subjects(("1", "Cables"), ("1.1", "Tools"), ("2", "2 m cable A"))
        selected = self.selection([dict(note_id="validation-a", post="Cable A is 2 m long. Tools.",
                                        teacher=teacher, answer=answer(student))])
        context = self.root / "assessment"
        assessment.record(selected, "R01", context, teacher_meanings=[
            dict(teacher_numbers=["1"], required=False), dict(teacher_numbers=["1.1"], required=True),
            dict(teacher_numbers=["2"], required=False)], reason="Independent fixture reference context.")
        worker = self.worker()
        worker.write_text(worker.read_text().replace('else {"valid": True, "reason": "Fixture semantic verdict."}',
                                                     'else {"valid": False, "reason": "Fixture semantic verdict."}'))
        prepared = evaluation.prepare(selected, self.root / "evaluation", runner_binary=worker, assessment_directory=context)
        for entry in prepared["experiments"]:
            self.native("run", entry["path"], "--max-new-attempts", 10)
        result = evaluation.report(self.root / "evaluation")["random"]["answers"][0]
        self.assertEqual(result["coverage"]["status"], "complete")
        self.assertEqual(result["scores"]["coverage"]["value"], 0)
        self.assertEqual(result["coverage"]["findings"][0]["matched_student_numbers"], ["2"])
        self.assertEqual(result["coverage"]["findings"][0]["missing_heading_numbers"], ["1"])
        self.assertEqual(result["scores"]["correctness"]["value"], 2 / 3)

    def test_changed_saved_sources_and_assessment_snapshot_reject_reporting(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        from sse_multivector import distillation_review_assessment as assessment
        selected = self.selection()
        context = self.root / "assessment"
        assessment.record(selected, "R01", context, teacher_meanings=[
            dict(teacher_numbers=["1"], required=False), dict(teacher_numbers=["1.1", "1.2"], required=True),
            dict(teacher_numbers=["1.3"], required=True), dict(teacher_numbers=["2"], required=False),
            dict(teacher_numbers=["2.1"], required=True)], reason="Frozen fixture source meanings.")
        evaluation.prepare(selected, self.root / "evaluation", runner_binary=self.worker(), assessment_directory=context)
        path = next(context.glob("teacher-*.json"))
        original = path.read_bytes()
        path.write_bytes(original + b"\n")
        with self.assertRaisesRegex(ValueError, "snapshot|hash"):
            evaluation.report(self.root / "evaluation")
        path.write_bytes(original)
        generation = Path(json.loads(selected.read_text())["random"]["answers"][0]["generation"]["path"])
        generation.write_bytes(generation.read_bytes() + b"\n")
        with self.assertRaisesRegex(ValueError, "hash"):
            evaluation.report(self.root / "evaluation")
        self.assertFalse((self.root / "calls.json").exists())

    def test_invalid_and_valid_empty_answers_preserve_zero_scores_without_dispatch(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        from sse_multivector import distillation_review_assessment as assessment
        teacher = subjects(("1", "Cables"), ("1.1", "2 m cable A"))
        for name, saved in (("invalid", answer([], raw="not JSON")), ("empty", answer([]))):
            with self.subTest(output=name):
                selected = self.selection([dict(note_id="validation-a", post="Cable A is 2 m long.",
                    teacher=teacher, answer=saved)], name=name)
                context = self.root / (name + "-assessment")
                assessment.record(selected, "R01", context, teacher_meanings=[
                    dict(teacher_numbers=["1"], required=False), dict(teacher_numbers=["1.1"], required=True)],
                    reason="Independent required source meaning.")
                output = self.root / (name + "-evaluation")
                prepared = evaluation.prepare(selected, output, runner_binary=self.worker(), assessment_directory=context)
                self.assertEqual(prepared["experiments"], [])
                result = evaluation.report(output)["random"]["answers"][0]
                self.assertEqual(result["status"], "invalid_output" if name == "invalid" else "complete")
                for metric in ("correctness", "coverage"):
                    self.assertEqual(result["scores"][metric]["value"], 0)
        self.assertFalse((self.root / "calls.json").exists())

    def test_frozen_expected_scores_and_case_qualifications_are_separate_from_prompts(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        from sse_multivector import distillation_review_assessment as assessment
        teacher = subjects(("1", "Cables"), ("1.1", "2 m cable A"))
        selected = self.selection([dict(note_id="validation-a", post="Cable A is 2 m long.",
                                        teacher=teacher, answer=answer(teacher))])
        context = self.root / "assessment"
        assessment.record(selected, "R01", context, teacher_meanings=[
            dict(teacher_numbers=["1"], required=False), dict(teacher_numbers=["1.1"], required=True)],
            reason="Independent fixture source meaning.")
        reason = "Frozen label outside every model input."
        assessment.record(selected, "R01", context, expectations=dict(
            matching=[dict(student_number=number, teacher_number=number, reason=reason) for number in ("1", "1.1")],
            support=[dict(student_number=number, valid=True, reason=reason) for number in ("1", "1.1")],
            relationships=[dict(child="1.1", valid=True, reason=reason)],
            compatibility=[dict(teacher_numbers=["1.1"], compatible_heading_numbers=["1", "1.1"], reason=reason)]),
            reason="Pre-call candidate judgments.")
        assessment.freeze(selected, context)
        prepared = evaluation.prepare(selected, self.root / "evaluation", runner_binary=self.worker(), assessment_directory=context)
        result = evaluation.report(self.root / "evaluation")
        row = result["random"]["answers"][0]
        self.assertEqual(row["expected_scores"], row["scores"])
        self.assertEqual(row["qualification"]["incorrect_cases"], [])
        self.assertEqual(row["qualification"]["score_differences"], {})
        self.assertEqual(row["qualification"]["unresolved"], [])
        self.assertEqual(result["summary"]["random"]["checks"]["relationship"]["mechanical"], 3)
        for entry in prepared["experiments"]:
            native = json.loads(self.native("show", entry["path"], "--json"))
            for case in native["cases"]:
                self.assertNotIn(reason, case["prompt"])
                self.assertIs(case["qualification"]["passed"], True)
        self.assertFalse((self.root / "calls.json").exists())

    def test_native_execution_errors_are_preserved_instead_of_allowance_exhaustion(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        from sse_multivector.extraction_pipeline import RunnerError
        evaluation.prepare(self.selection(), self.root / "evaluation", runner_binary=self.worker())
        with patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.root / "calls.json"), FAKE_RUNNER_FAIL_STAGE="prompt"):
            with self.assertRaises(RunnerError):
                evaluation.run(self.root / "evaluation", max_new_attempts=10)
        report = evaluation.report(self.root / "evaluation")
        self.assertEqual(report["random"]["answers"][0]["status"], "failed")
        self.assertEqual(len(json.loads((self.root / "calls.json").read_text())), 6)
        records = [json.loads(line) for native in report["experiments"]
                   for path in (Path(native["experiment"]) / "run/results.jsonl",)
                   if path.exists() for line in path.read_text().splitlines()]
        self.assertEqual(len(records), 6)
        self.assertTrue(all(record["attempt"] == 1 and "retry_reason" not in record for record in records))

    def test_no_match_and_unsupported_child_skip_questions_without_inventing_verdicts(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        from sse_multivector import distillation_review_assessment as assessment
        teacher = subjects(("1", "Cables"), ("1.1", "Cable A"))
        student = subjects(("1", "Unrelated root"), ("1.1", "Unrelated child"))
        selected = self.selection([dict(note_id="validation-a", post="Cable A.",
            teacher=teacher, answer=answer(student))])
        context = self.root / "assessment"
        assessment.record(selected, "R01", context, teacher_meanings=[
            dict(teacher_numbers=["1"], required=False), dict(teacher_numbers=["1.1"], required=True)],
            reason="Independent complete source meaning.")
        worker = self.worker()
        worker.write_text(worker.read_text().replace('else {"valid": True, "reason": "Fixture semantic verdict."}',
            'else {"valid": False, "reason": "Fixture semantic verdict."}'))
        evaluation.prepare(selected, self.root / "evaluation", runner_binary=worker, assessment_directory=context)
        with patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.root / "calls.json")):
            report = evaluation.run(self.root / "evaluation", max_new_attempts=20)
        self.assertEqual(len(json.loads((self.root / "calls.json").read_text())), 4)
        row = report["random"]["answers"][0]
        self.assertEqual(row["status"], "complete")
        self.assertEqual({key: value["value"] for key, value in row["scores"].items()},
                         dict(correctness=0, coverage=0))
        skipped = [case for case in row["checks"]["relationship"] if case["status"] == "skipped"]
        self.assertEqual(len(skipped), 3)
        self.assertEqual({case["skip_evidence"]["rule"] for case in skipped},
                         {"no_full_match", "unsupported_child"})
        self.assertTrue(all(case.get("parsed") is None and not case.get("qualification", {}).get("passed")
                            for case in skipped))
        self.assertEqual(report["summary"]["requests"]["totals"]["new"], 0)

    def test_trusted_uncovered_witness_stops_other_placement_calls(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        from sse_multivector import distillation_review_assessment as assessment
        teacher = subjects(("1", "Cables"), ("1.1", "Cable A"))
        student = subjects(("1", "Cables"), ("2", "Cable A"), ("3", "Other wording"))
        selected = self.selection([dict(note_id="validation-a", post="Cable A.",
            teacher=teacher, answer=answer(student))])
        context = self.root / "assessment"
        assessment.record(selected, "R01", context, teacher_meanings=[
            dict(teacher_numbers=["1"], required=False), dict(teacher_numbers=["1.1"], required=True)],
            reason="Independent complete source meaning.")
        evaluation.prepare(selected, self.root / "evaluation", runner_binary=self.worker(), assessment_directory=context)
        with patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.root / "calls.json")):
            report = evaluation.run(self.root / "evaluation", max_new_attempts=20)
        self.assertEqual(len(json.loads((self.root / "calls.json").read_text())), 2)
        row = report["random"]["answers"][0]
        self.assertEqual(row["scores"]["coverage"]["value"], 0)
        skipped = [case for case in row["checks"]["relationship"] if case["status"] == "skipped"]
        self.assertEqual(len(skipped), 1)
        self.assertEqual(skipped[0]["skip_evidence"]["rule"], "uncovered_compatible_heading")
        self.assertTrue(skipped[0]["skip_evidence"]["depends_on"])

    def test_first_semantic_uncovered_witness_stops_further_calls(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        from sse_multivector import distillation_review_assessment as assessment
        teacher = subjects(("1", "Cable A"))
        student = subjects(("1", "First other wording"), ("2", "Second other wording"),
                           ("3", "Cable A"), ("4", "Third other wording"))
        selected = self.selection([dict(note_id="validation-a", post="Cable A.",
            teacher=teacher, answer=answer(student))])
        context = self.root / "assessment"
        assessment.record(selected, "R01", context, teacher_meanings=[dict(teacher_numbers=["1"], required=True)],
                          reason="Independent complete source meaning.")
        evaluation.prepare(selected, self.root / "evaluation", runner_binary=self.worker(), assessment_directory=context)
        with patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.root / "calls.json")):
            report = evaluation.run(self.root / "evaluation", max_new_attempts=20)
        self.assertEqual(len(json.loads((self.root / "calls.json").read_text())), 7)
        row = report["random"]["answers"][0]
        self.assertEqual(row["scores"]["coverage"]["value"], 0)
        self.assertEqual(sum(case["status"] == "skipped" for case in row["checks"]["relationship"]), 2)
        self.assertEqual(row["qualification"]["status"], "pending")

    def test_matching_self_contradiction_is_checked_after_trusted_coverage_failure(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        from sse_multivector import distillation_review_assessment as assessment
        teacher = subjects(("1", "Cables"), ("1.1", "Cable A"))
        student = subjects(("1", "Cables"), ("2", "Paraphrase of Cable A"))
        selected = self.selection([dict(note_id="validation-a", post="Cable A.",
            teacher=teacher, answer=answer(student))])
        context = self.root / "assessment"
        assessment.record(selected, "R01", context, teacher_meanings=[
            dict(teacher_numbers=["1"], required=False), dict(teacher_numbers=["1.1"], required=True)],
            reason="Independent complete source meaning.")
        worker = self.worker()
        worker.write_text(worker.read_text().replace('{"teacher_id": None, "reason": "Fixture unmatched wording."}',
            '{"teacher_id": "T02", "reason": "Fixture full match."}').replace(
            'else {"valid": True, "reason": "Fixture semantic verdict."}',
            'else {"valid": not prompt.startswith("DSLv2"), "reason": "Fixture semantic verdict."}'))
        evaluation.prepare(selected, self.root / "evaluation", runner_binary=worker, assessment_directory=context)
        with patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.root / "calls.json")):
            report = evaluation.run(self.root / "evaluation", max_new_attempts=20)
        row = report["random"]["answers"][0]
        self.assertEqual(len(json.loads((self.root / "calls.json").read_text())), 3)
        self.assertEqual(row["status"], "inconsistent_verdicts")
        self.assertNotIn("scores", row)
        self.assertEqual(row["qualification"]["status"], "failed")
        self.assertEqual([case["parsed"]["valid"] for case in row["checks"]["relationship"]
                          if case["evidence"]["heading_number"] == "2"], [False])

    def test_covered_ancestors_skip_placements_but_retain_shared_actual_edge_requests(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        from sse_multivector import distillation_review_assessment as assessment
        teacher = subjects(("1", "Cable A"))
        student = subjects(("1", "New root"), ("1.1", "New parent"), ("1.1.1", "Cable A"))
        selected = self.selection([dict(note_id="validation-a", post="Cable A.",
            teacher=teacher, answer=answer(student))])
        context = self.root / "assessment"
        assessment.record(selected, "R01", context, teacher_meanings=[dict(teacher_numbers=["1"], required=True)],
                          reason="Independent complete source meaning.")
        evaluation.prepare(selected, self.root / "evaluation", runner_binary=self.worker(), assessment_directory=context)
        with patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.root / "calls.json")):
            report = evaluation.run(self.root / "evaluation", max_new_attempts=20)
        self.assertEqual(len(json.loads((self.root / "calls.json").read_text())), 6)
        row = report["random"]["answers"][0]
        self.assertEqual(row["scores"]["coverage"]["value"], 1)
        self.assertEqual(row["scores"]["correctness"]["value"], 1)
        self.assertTrue(all(case["status"] == "valid" for case in row["checks"]["relationship"]
                            if case["evidence"]["role"] == "actual_relationship"))
        skipped = [case for case in row["checks"]["relationship"] if case["status"] == "skipped"]
        self.assertEqual(len(skipped), 1)
        self.assertEqual(skipped[0]["skip_evidence"]["rule"], "match_beneath_heading")
        shared = [case for case in row["checks"]["relationship"]
                  if case["evidence"].get("heading_number") == "1.1"]
        self.assertEqual(shared[0]["status"], "valid")
        aliases = [case for case in row["checks"]["relationship"]
                   if case["input_sha256"] == shared[0]["input_sha256"]]
        self.assertEqual(sum(case["reused"] for case in aliases), 1)
        self.assertEqual(aliases[0]["parsed"], aliases[1]["parsed"])

    def test_no_positive_uncovered_witness_requires_every_remaining_placement(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        from sse_multivector import distillation_review_assessment as assessment
        teacher = subjects(("1", "Cable A"))
        student = subjects(("1", "First other wording"), ("2", "Second other wording"), ("3", "Cable A"))
        selected = self.selection([dict(note_id="validation-a", post="Cable A.",
            teacher=teacher, answer=answer(student))])
        context = self.root / "assessment"
        assessment.record(selected, "R01", context, teacher_meanings=[dict(teacher_numbers=["1"], required=True)],
                          reason="Independent complete source meaning.")
        worker = self.worker()
        worker.write_text(worker.read_text().replace('else {"valid": True, "reason": "Fixture semantic verdict."}',
            'else {"valid": not prompt.startswith("DSLv2"), "reason": "Fixture semantic verdict."}'))
        evaluation.prepare(selected, self.root / "evaluation", runner_binary=worker, assessment_directory=context)
        with patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.root / "calls.json")):
            report = evaluation.run(self.root / "evaluation", max_new_attempts=20)
        self.assertEqual(len(json.loads((self.root / "calls.json").read_text())), 6)
        row = report["random"]["answers"][0]
        self.assertEqual(row["scores"]["coverage"]["value"], 1)
        self.assertTrue(all(case["status"] == "valid" for case in row["checks"]["relationship"]))

    def test_zero_allowance_joins_saved_receipts_without_new_calls(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        selected, worker = self.selection(), self.worker()
        first, second = self.root / "first", self.root / "second"
        evaluation.prepare(selected, first, runner_binary=worker, history_root=self.root)
        with patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.root / "calls.json")):
            evaluation.run(first, max_new_attempts=10)
            evaluation.prepare(selected, second, runner_binary=worker, history_root=self.root)
            report = evaluation.run(second, max_new_attempts=0)
        self.assertEqual(len(json.loads((self.root / "calls.json").read_text())), 10)
        self.assertEqual(report["random"]["answers"][0]["status"], "complete")
        self.assertEqual(report["generation_usage"]["original_calls"], 10)
        self.assertEqual(report["summary"]["requests"]["totals"]["new"], 0)

    def test_cached_later_witness_is_reused_before_a_fresh_earlier_question(self):
        from experiment_runner import experiment
        from sse_multivector import distillation_review_evaluation as evaluation
        from sse_multivector import distillation_review_assessment as assessment
        teacher = subjects(("1", "Cable A"))
        student = subjects(("1", "Fresh first heading"), ("2", "Cached compatible heading"), ("3", "Cable A"))
        selected = self.selection([dict(note_id="validation-a", post="Cable A.",
            teacher=teacher, answer=answer(student))])
        context = self.root / "assessment"
        assessment.record(selected, "R01", context, teacher_meanings=[dict(teacher_numbers=["1"], required=True)],
                          reason="Independent complete source meaning.")
        first, second = self.root / "first", self.root / "second"
        prepared = evaluation.prepare(selected, first, runner_binary=self.worker(),
            history_root=self.root, assessment_directory=context)
        with patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.root / "calls.json")):
            for entry in prepared["experiments"]:
                if entry["check"] != "relationship":
                    experiment.run(Path(entry["path"]), 20)
                else:
                    rows = experiment.report(Path(entry["path"]), include_request_preview=False)["cases"]
                    cached = next(row["id"] for row in rows if row["evidence"]["heading_number"] == "2")
                    experiment.run(Path(entry["path"]), 1, only=[cached])
            self.assertEqual(len(json.loads((self.root / "calls.json").read_text())), 5)
            evaluation.prepare(selected, second, runner_binary=self.worker(),
                history_root=self.root, assessment_directory=context)
            report = evaluation.run(second, max_new_attempts=20)
        self.assertEqual(len(json.loads((self.root / "calls.json").read_text())), 5)
        row = report["random"]["answers"][0]
        self.assertEqual(row["scores"]["coverage"]["value"], 0)
        self.assertEqual(next(case["status"] for case in row["checks"]["relationship"]
                              if case["evidence"]["heading_number"] == "1"), "skipped")


if __name__ == "__main__":
    unittest.main()
