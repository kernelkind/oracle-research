"""Offline coordinator integration using the production adapters and runner."""

import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from sse_multivector.bounded_hierarchy_build import prepare_build, report_build, run_build
from sse_multivector import bounded_hierarchy_build as build
from sse_multivector.bounded_hierarchy_workflow import DISCOVERY_SCHEMA, COMPARISON_SCHEMA
from sse_multivector.test_extraction_pipeline import FAKE_RUNNER
from sse_multivector import test_subject_matching_probe as saved_matching


class BoundedHierarchyBuildTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        source, probe = saved_matching.SavedMatchingTests().fixture(self.root)
        inputs = json.loads((probe / "inputs.json").read_text())
        for entry in inputs["subjects"]:
            entry["context"] = "source context for " + entry["subject"]
        self.write("inputs.json", inputs)
        self.write("hierarchy.json", dict(experiment_id="original-LG01", groups=[[i] for i in range(4)],
                                         member_to_group=list(range(4)), edges=inputs["edges"]))
        self.runner = self.root / "runner"
        runner = FAKE_RUNNER.replace(
            'output_text = os.environ.get(\n        "FAKE_RUNNER_PROMPT_RESPONSE", f"Response to: {prompt}"\n    )',
            '''payload = json.loads(prompt.split("\\n", 1)[1])
    if "queries" in payload:
        queries = []
        for q in payload["queries"]:
            candidates = []
            if os.environ.get("BUILD_NOMINATE") == "1" and q["id"] == "S0000":
                candidates = [{"id": "S0002", "reason": "same Bread meaning"}]
            queries.append({"id": q["id"], "candidates": candidates})
        output_text = json.dumps({"queries": queries})
    else:
        comparisons = [{"id": p["id"], "relation": "equivalent", "reason": "same meaning"}
                       for p in payload["pairs"]]
        if os.environ.get("BUILD_INVALID_COMPARISON") == "1":
            comparisons = []
        output_text = json.dumps({"comparisons": comparisons})''')
        self.runner.write_text(runner)
        self.runner.chmod(0o755)
        (self.root / "discovery.txt").write_text("GENERIC PROMPT DISCOVERY\n{INPUT_JSON}")
        (self.root / "comparison.txt").write_text("GENERIC PROMPT COMPARISON\n{INPUT_JSON}")
        self.spec = self.write("spec.json", dict(schema_version=1, id="HG100-SOL01",
            inputs="inputs.json", hierarchy="hierarchy.json", subject_probe=str(probe),
            source=str(source), prompts=dict(discovery=dict(id="PCPv2", path="discovery.txt"),
            comparison=dict(id="BCPv5", path="comparison.txt")), runner=dict(
            runner_binary=str(self.runner), provider="openai-codex", model="gpt-6.1-sol",
            reasoning_effort="low", timeout_seconds=600),
            max_model_calls=2000, max_passes=3, max_nominations_per_reference=9,
            work_budget=20000))
        self.directory = self.root / "build"
        self.environment = patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.root / "calls.json"))
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def write(self, name, value):
        path = self.root / name
        path.write_text(json.dumps(value))
        return path

    def test_prepare_uses_shared_jobs_offline_and_freezes_sources(self):
        summary = prepare_build(self.spec, self.directory)
        self.assertEqual(summary["id"], "HG100-SOL01")
        self.assertEqual(summary["model_calls"], 0)
        self.assertEqual(summary["status"], "prepared")
        self.assertEqual((self.directory / ".gitignore").read_text(), "*\n")
        self.assertTrue((self.directory / "passes" / "01" / "discovery" / "experiment.json").exists())
        self.assertFalse((self.root / "calls.json").exists())
        self.assertEqual(report_build(self.directory), summary)
        child = json.loads((self.directory / "passes" / "01" / "discovery" / "experiment.json").read_text())["plan"]
        self.assertEqual(child["runner"]["output_schema"], DISCOVERY_SCHEMA)
        self.assertEqual(child.get('publication_role'), 'internal')
        self.assertFalse((self.directory/'passes/01/discovery/publication').exists())

    def test_zero_nomination_pass_finishes_without_preparing_empty_runner_batch(self):
        prepare_build(self.spec, self.directory)
        summary = run_build(self.directory)
        self.assertEqual(summary["status"], "finished")
        self.assertEqual(summary["stop_reason"], "no_graph_change")
        self.assertEqual(summary["passes"], 1)
        self.assertEqual(summary["subjects"], 4)
        self.assertTrue(Path(summary["export"]).joinpath("categories.json").exists())
        calls = json.loads((self.root / "calls.json").read_text())
        self.assertEqual(summary["model_calls"], len(calls))
        self.assertEqual(run_build(self.directory), summary)
        self.assertEqual(json.loads((self.root / "calls.json").read_text()), calls)

    def test_exhausted_global_budget_still_exports_and_reports_unrun_work(self):
        value = json.loads(self.spec.read_text())
        value["max_model_calls"] = 1
        self.spec.write_text(json.dumps(value))
        prepare_build(self.spec, self.directory)
        self.write("build/budget.json", dict(schema_version=1, limit=1, used=1))
        summary = run_build(self.directory)
        self.assertEqual(summary["status"], "unfinished")
        self.assertEqual(summary["stop_reason"], "model_call_budget")
        self.assertGreater(summary["unresolved_cases"], 0)
        self.assertTrue(Path(summary["export"]).joinpath("categories.json").exists())
        self.assertFalse((self.root / "calls.json").exists())

    def test_source_change_is_rejected_before_any_request(self):
        prepare_build(self.spec, self.directory)
        with (self.root / "inputs.json").open("a") as source:
            source.write("\n")
        with self.assertRaisesRegex(ValueError, "source changed"):
            run_build(self.directory)
        self.assertFalse((self.root / "calls.json").exists())

    def test_policy_cannot_exceed_authorized_call_or_pass_limits(self):
        for key, value in (("max_model_calls", 2001), ("max_passes", 4),
                           ("max_nominations_per_reference", 10)):
            spec = json.loads(self.spec.read_text())
            spec[key] = value
            self.spec.write_text(json.dumps(spec))
            with self.subTest(key=key), self.assertRaises(ValueError):
                prepare_build(self.spec, self.directory)
            self.assertFalse(self.directory.exists())

    def test_crash_after_export_resumes_without_overwriting_snapshot(self):
        prepare_build(self.spec, self.directory)
        original_save = build._save

        def interrupted(directory, plan):
            if plan["export"]:
                raise OSError("simulated interruption after export")
            return original_save(directory, plan)

        with patch.object(build, "_save", side_effect=interrupted):
            with self.assertRaisesRegex(OSError, "simulated interruption"):
                run_build(self.directory)
        output = self.directory / "exports" / "pass-01-001"
        snapshots = {p.name: p.read_bytes() for p in output.iterdir()}
        summary = run_build(self.directory)
        self.assertEqual(summary["status"], "finished")
        self.assertEqual(snapshots, {p.name: p.read_bytes() for p in output.iterdir()})

    def test_positive_comparison_resumes_after_invocation_limit_with_receipt(self):
        spec = json.loads(self.spec.read_text())
        spec["max_passes"] = 1
        self.spec.write_text(json.dumps(spec))
        prepare_build(self.spec, self.directory)
        with patch.dict(os.environ, BUILD_NOMINATE="1"):
            partial = run_build(self.directory, max_new_attempts=2)
            self.assertEqual(partial["status"], "unfinished")
            self.assertEqual(partial["stop_reason"], "invocation_limit")
            self.assertGreater(partial["unresolved_cases"], 0)
            summary = run_build(self.directory)
        self.assertEqual(summary["status"], "finished")
        self.assertEqual(summary["stop_reason"], "pass_limit")
        self.assertEqual(summary["nodes"], 3)
        self.assertEqual(summary["comparisons"], 1)
        manifest = json.loads((self.directory / "bounded-build.json").read_text())["plan"]
        self.assertTrue(manifest["comparisons"][0]["receipt"]["record_sha256"])
        child = json.loads((self.directory / "passes" / "01" / "comparison" / "experiment.json").read_text())["plan"]
        self.assertEqual(child["runner"]["output_schema"], COMPARISON_SCHEMA)
        provenance = json.loads((Path(summary["export"]) / "provenance.json").read_text())
        self.assertEqual(len(provenance["subjects"]), 4)
        self.assertEqual(len(provenance["masks"]), 2)
        self.assertEqual(provenance["baseline"]["status"], "finished")
        self.assertEqual(provenance["baseline"]["stop_reason"], "pass_limit")

    def test_invalid_comparison_stays_unfinished_and_is_not_automatically_retried(self):
        prepare_build(self.spec, self.directory)
        with patch.dict(os.environ, BUILD_NOMINATE="1", BUILD_INVALID_COMPARISON="1"):
            summary = run_build(self.directory)
            self.assertEqual(summary["status"], "unfinished")
            self.assertEqual(summary["stop_reason"], "partial_failure")
            self.assertEqual(summary["comparisons"], 0)
            self.assertGreater(summary["unresolved_cases"], 0)
            calls = json.loads((self.root / "calls.json").read_text())
            self.assertEqual(run_build(self.directory), summary)
            self.assertEqual(json.loads((self.root / "calls.json").read_text()), calls)


if __name__ == "__main__":
    unittest.main()
