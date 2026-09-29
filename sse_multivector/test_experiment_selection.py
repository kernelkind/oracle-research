"""Read-only case selection must scope both output and accounted attempts."""
import json
import os
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
        self.cli("show", "imported", "--note", "absent", ok=False)
        self.cli("show", "imported", "--note", "N1", "--note", "N1", ok=False)


if __name__ == "__main__":
    unittest.main()
