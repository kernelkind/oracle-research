"""Read-only case selection must scope both output and accounted attempts."""
import json
import os
import subprocess
import unittest
from unittest.mock import patch

from sse_multivector import test_experiment as fixtures
from sse_multivector import extraction_pipeline as engine


class ExperimentSelectionTests(unittest.TestCase):
    setUp = fixtures.ExperimentTests.setUp
    write = fixtures.ExperimentTests.write
    cli = fixtures.ExperimentTests.cli
    prepare = fixtures.ExperimentTests.prepare
    show = fixtures.ExperimentTests.show
    calls = fixtures.ExperimentTests.calls
    mask_spec = fixtures.ExperimentTests.mask_spec

    def test_show_only_scopes_usage_and_validates_ids_without_inference(self):
        self.prepare()
        self.cli("run", "E1", env={"FAKE_RUNNER_RESULT_OVERRIDE": json.dumps({
            "usage": {"input": 11, "cacheRead": 7, "cacheWrite": 0,
                      "output": 5, "reasoning": 3, "cost": {"total": 0.1}},
            "response_metadata": {"usage": {"cost": 0.1}}})})
        report = self.show("E1", "--only", "one")
        self.assertEqual([c["id"] for c in report["cases"]], ["one"])
        self.assertEqual(report["summary"]["attempts"], 1)
        self.assertEqual(report["usage"]["input_tokens"], 11)
        self.assertEqual(report["usage"]["cached_input_tokens"], 7)
        self.assertEqual(report["usage"]["output_tokens"], 5)
        self.assertEqual(report["usage"]["provider_reported_cost_usd"], 0.1)
        self.assertGreaterEqual(report["cases"][0]["elapsed_seconds"], 0)
        self.assertEqual(self.show()["summary"]["attempts"], 2)
        self.cli("show", "E1", "--only", "absent", ok=False)
        self.cli("show", "E1", "--only", "one", "--only", "one", ok=False)
        self.assertEqual(len(self.calls()), 2)

    def test_generation_costs_trace_sources_once_without_new_inference_or_spend(self):
        data = json.loads(self.cases.read_text())
        data["cases"].append({"id": "duplicate", "inputs": data["cases"][0]["inputs"]})
        self.write("cases.json", data)
        self.prepare()
        self.cli("run", "E1", env={"FAKE_RUNNER_RESULT_OVERRIDE": json.dumps({
            "usage": {"input": 11, "cacheRead": 7, "cacheWrite": 0,
                      "output": 5, "reasoning": 3, "cost": {"total": 0.1}},
            "response_metadata": {"usage": {"cost": 0.1}}})})
        self.cli("prepare", "E2", "--from", "E1")
        self.cli("run", "E2")
        paths = [self.root / name / "run/results.jsonl" for name in ("E1", "E2")]
        before = [p.read_bytes() for p in paths]
        report = self.show("E2", "--generation-costs")
        self.assertEqual(report["summary"]["reused"], 3)
        self.assertEqual(report["usage"]["input_tokens"], 0)
        self.assertEqual(report["usage"]["catalog_cost_estimate_usd"], 0)
        generation = report["generation_usage"]
        self.assertEqual(generation["original_calls"], 2)
        self.assertEqual(generation["source_calls_added"], 2)
        self.assertEqual(generation["input_tokens"], 22)
        self.assertEqual(generation["cached_input_tokens"], 14)
        self.assertEqual(generation["output_tokens"], 10)
        self.assertEqual(generation["reasoning_tokens"], 6)
        self.assertAlmostEqual(generation["catalog_cost_estimate_usd"], 0.2)
        self.assertAlmostEqual(generation["provider_reported_cost_usd"], 0.2)
        selected = self.show("E2", "--generation-costs", "--only", "duplicate")
        self.assertEqual(selected["generation_usage"]["original_calls"], 1)
        self.assertEqual(selected["generation_usage"]["cached_input_tokens"], 7)
        # A source already charged in this run must not be counted again.
        local = self.show("E1", "--generation-costs")
        self.assertEqual(local["generation_usage"]["original_calls"], 2)
        self.assertEqual(local["generation_usage"]["source_calls_added"], 0)
        self.assertEqual([p.read_bytes() for p in paths], before)
        self.assertEqual(len(self.calls()), 2)

    def test_generation_costs_mix_fresh_calls_with_reused_sources(self):
        self.prepare()
        result = {"usage": {"input": 11, "cacheRead": 7, "output": 5,
                            "cost": {"total": 0.1}}}
        self.cli("run", "E1", env={"FAKE_RUNNER_RESULT_OVERRIDE": json.dumps(result)})
        data = json.loads(self.cases.read_text())
        data["cases"].append({"id": "three", "inputs": {"POST": "Third"}})
        self.write("cases.json", data)
        self.prepare("E2")
        result["usage"]["cost"]["total"] = 0.2
        self.cli("run", "E2", env={"FAKE_RUNNER_RESULT_OVERRIDE": json.dumps(result)})
        report = self.show("E2", "--generation-costs")
        self.assertEqual(report["summary"]["attempts"], 1)
        self.assertEqual(report["generation_usage"]["original_calls"], 3)
        self.assertEqual(report["generation_usage"]["source_calls_added"], 2)
        self.assertAlmostEqual(report["usage"]["catalog_cost_estimate_usd"], 0.2)
        self.assertAlmostEqual(report["generation_usage"]["catalog_cost_estimate_usd"], 0.4)
        case = self.show("E2", "--generation-costs", "--case", "one")
        self.assertEqual(case["generation_usage"]["original_calls"], 1)
        plain = self.cli("show", "E2", "--generation-costs").stdout
        self.assertIn("Generation usage", plain)
        self.assertEqual(len(self.calls()), 3)

    def test_generation_costs_keep_zero_normalized_failure_usage_unknown(self):
        self.prepare()
        self.cli("run", "E1", "--max-new-attempts", "1", ok=False, env={
            "FAKE_RUNNER_RESULT_OVERRIDE": json.dumps({"usage": {
                "input": 0, "cacheRead": 0, "output": 0, "cost": {"total": 0}}}),
            "FAKE_RUNNER_FAILURES": json.dumps({"Tea": {
                "metadata": {"http_status": 200}, "error": "terminated"}})})
        self.cli("run", "E1", ok=False, env={"FAKE_RUNNER_RESULT_OVERRIDE": json.dumps({
            "usage": {"input": 11, "cacheRead": 7, "output": 5,
                      "cost": {"total": 0.1}},
            "response_metadata": {"usage": {"cost": 0.1}}})})
        report = self.show("E1", "--generation-costs")
        generation = report["generation_usage"]
        self.assertEqual(generation["original_calls"], 2)
        self.assertEqual(generation["failed_calls"], 1)
        self.assertEqual(generation["attempts_without_usage"], 1)
        self.assertIsNone(generation["catalog_cost_estimate_usd"])
        self.assertAlmostEqual(generation["known_catalog_cost_estimate_usd"], 0.1)
        self.assertIsNone(generation["provider_reported_cost_usd"])
        self.assertAlmostEqual(generation["known_provider_reported_cost_usd"], 0.1)
        self.assertEqual(generation["input_tokens"], 11)
        self.assertAlmostEqual(report["usage"]["catalog_cost_estimate_usd"], 0.1)
        selected = self.show("E1", "--generation-costs", "--only", "two")
        self.assertEqual(selected["generation_usage"]["attempts_without_usage"], 0)
        self.assertEqual(len(self.calls()), 2)

    def test_generation_costs_preserve_distinct_calls_and_reported_failure_tokens(self):
        data = json.loads(self.cases.read_text())
        data["cases"][1]["inputs"] = data["cases"][0]["inputs"]
        self.write("cases.json", data)
        self.prepare("E1", "--repeat")
        self.cli("run", "E1", env={"FAKE_RUNNER_RESULT_OVERRIDE": json.dumps({
            "usage": {"input": 11, "output": 5, "cost": {"total": 0.1}}})})
        generation = self.show("E1", "--generation-costs")["generation_usage"]
        self.assertEqual(generation["original_calls"], 2)
        self.assertAlmostEqual(generation["catalog_cost_estimate_usd"], 0.2)
        self.prepare("E2", "--repeat")
        self.cli("run", "E2", ok=False, env={
            "FAKE_RUNNER_RESULT_OVERRIDE": json.dumps({
                "usage": {"input": 11, "output": 5, "cost": {"total": 0.1}}}),
            "FAKE_RUNNER_FAILURES": json.dumps({"Tea": {
                "metadata": {"http_status": 200}, "error": "terminated"}})})
        generation = self.show("E2", "--generation-costs")["generation_usage"]
        self.assertEqual(generation["failed_calls"], 2)
        self.assertEqual(generation["attempts_without_usage"], 0)
        self.assertEqual(generation["input_tokens"], 22)
        self.assertAlmostEqual(generation["catalog_cost_estimate_usd"], 0.2)
        self.assertEqual(len(self.calls()), 4)

    def test_generation_costs_refuse_tampered_sources_without_inference(self):
        self.prepare()
        self.cli("run", "E1")
        self.cli("prepare", "E2", "--from", "E1")
        self.cli("run", "E2")
        source = self.root / "E1/run/results.jsonl"
        source.write_bytes(source.read_bytes().replace(b"Tea", b"Bad"))
        result = self.cli("show", "E2", "--generation-costs", "--json", ok=False)
        self.assertIn("source", result.stderr)
        self.assertEqual(len(self.calls()), 2)

    def test_generation_costs_keep_retry_attempts_not_just_final_answers(self):
        self.prepare()
        self.cli("run", "E1", env={
            "FAKE_RUNNER_RESULT_OVERRIDE": json.dumps({
                "usage": {"input": 11, "output": 5, "cost": {"total": 0.1}}}),
            "FAKE_RUNNER_FAILURES": json.dumps({"Tea": {
                "metadata": {"http_status": 504}, "attempts": 1}})})
        generation = self.show("E1", "--generation-costs", "--only", "one")["generation_usage"]
        self.assertEqual(generation["original_calls"], 2)
        self.assertEqual(generation["failed_calls"], 1)
        self.assertAlmostEqual(generation["catalog_cost_estimate_usd"], 0.2)
        self.cli("prepare", "E2", "--from", "E1")
        self.cli("run", "E2")
        # An externally reused answer needed the source's failed attempt too.
        generation = self.show("E2", "--generation-costs")["generation_usage"]
        self.assertEqual(generation["original_calls"], 3)
        self.assertEqual(generation["failed_calls"], 1)
        self.assertAlmostEqual(generation["catalog_cost_estimate_usd"], 0.3)
        self.assertEqual(len(self.calls()), 3)

    def test_generation_costs_do_not_coerce_missing_or_boolean_usage_to_zero(self):
        self.prepare()
        self.cli("run", "E1", env={"FAKE_RUNNER_RESULT_OVERRIDE": json.dumps({
            "usage": {"input": False, "output": 5, "cost": {"total": 0.1}}})})
        generation = self.show("E1", "--generation-costs")["generation_usage"]
        self.assertEqual(generation["attempts_without_usage"], 2)
        self.assertIsNone(generation["catalog_cost_estimate_usd"])
        self.assertEqual(generation["known_catalog_cost_estimate_usd"], 0)
        self.cli("prepare", "E2", "--from", "E1", "--repeat")
        self.cli("run", "E2", env={"FAKE_RUNNER_RESULT_OVERRIDE": json.dumps({
            "usage": {"output": 5, "cost": {"total": 0.1}}})})
        generation = self.show("E2", "--generation-costs")["generation_usage"]
        self.assertEqual(generation["attempts_without_usage"], 2)
        self.assertIsNone(generation["catalog_cost_estimate_usd"])
        self.assertEqual(len(self.calls()), 4)

    def test_generation_costs_use_verified_reconciled_source_billing(self):
        from sse_multivector import experiment
        spec = json.loads(self.spec.read_text())
        spec["runner"]["provider"] = "openrouter"
        self.write("spec.json", spec)
        self.prepare("E1", "--only", "one")
        self.cli("run", "E1", env={"FAKE_RUNNER_RESULT_OVERRIDE": json.dumps({
            "usage": {"input": 11, "output": 5, "cost": {"total": 0.1}},
            "response_metadata": {"id": "gen-test"}})})
        reply = subprocess.CompletedProcess([], 0, json.dumps([
            {"id": "gen-test", "total_cost": 0.08, "model": "fixture/model"}]), "")
        with patch.object(experiment.subprocess, "run", return_value=reply):
            experiment.reconcile_costs(self.root / "E1")
        billing = self.root / "E1/run/cost-receipts.jsonl"
        before = billing.read_bytes()
        self.cli("prepare", "E2", "--from", "E1")
        self.cli("run", "E2")
        report = self.show("E2", "--generation-costs")
        self.assertEqual(report["usage"]["provider_reported_cost_usd"], 0)
        self.assertEqual(report["generation_usage"]["original_calls"], 1)
        self.assertAlmostEqual(report["generation_usage"]["provider_reported_cost_usd"], 0.08)
        self.assertAlmostEqual(report["generation_usage"]["catalog_cost_estimate_usd"], 0.1)
        self.assertEqual(billing.read_bytes(), before)
        self.assertEqual(len(self.calls()), 1)

    def test_duplicate_saved_subjects_prepare_and_import_by_original_item_id(self):
        self.mask_spec()
        source = json.loads(self.cases.read_text())
        source["notes"][0]["subjects"][1]["subject"] = "Tea"
        self.cases.write_text(json.dumps(source))
        self.prepare()
        report = self.show()
        self.assertEqual(len({c["id"] for c in report["cases"]}), 2)
        spec = json.loads(self.spec.read_text())
        legacy = {"schema_version": 1, **spec["runner"],
            "input_path": str(self.cases), "prompt_path": str(self.prompt),
            "run_directory": str(self.root / "legacy-run"),
            "mask_format": "word_positions", "timeout_seconds": 600}
        schema = {"type": "object", "properties": {"meaning": {"type": "string"},
            "expressible": {"type": "boolean"}, "evidence": {"type": "string"},
            "mask": {"type": "array"}}, "required": ["meaning", "expressible", "evidence", "mask"]}
        legacy["output_schema"] = schema
        path = self.write("legacy.json", legacy)
        with patch.dict(os.environ, {"FAKE_RUNNER_LOG": str(self.log),
            "FAKE_RUNNER_PROMPT_RESPONSE": json.dumps({"meaning": "Tea",
                "expressible": False, "evidence": "none", "mask": []})}):
            engine.run_masks(path)
        spec["runner"]["output_schema"] = dict(reversed(list(schema.items())))
        self.spec.write_text(json.dumps(spec))
        self.cli("prepare", "imported", "--spec", self.spec, "--import-config", path)
        imported = self.show("imported")
        self.assertEqual([c["job_id"] for c in imported["cases"]], ["M001", "M002"])
        self.assertEqual(imported["summary"]["empty"], 2)
        selected = self.show("imported", "--note", "N1")
        self.assertEqual(selected["summary"]["attempts"], 1)
        self.assertEqual(selected["summary"]["reused"], 1)
        generation = self.show("imported", "--generation-costs",
                               "--only", imported["cases"][1]["id"])["generation_usage"]
        self.assertEqual(generation["original_calls"], 1)
        self.assertEqual(generation["source_calls_added"], 1)
        self.assertEqual(generation["input_tokens"], 100)
        self.cli("show", "imported", "--note", "absent", ok=False)
        self.cli("show", "imported", "--note", "N1", "--note", "N1", ok=False)


if __name__ == "__main__":
    unittest.main()
