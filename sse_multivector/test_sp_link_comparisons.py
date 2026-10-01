"""Original SP links use the shared BCPv5 preparation and validation paths."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from sse_multivector import experiment_inputs as inputs


class SPLinkComparisonTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = dict(
            posts=[dict(note_id="p1", note_short_id="N001", text="Rice and butter.")],
            subjects=[dict(index=i, number=number, subject=subject, context=context,
                           note_id="p1", note_short_id="N001", fragments=[],
                           byte_spans=[], mask_vector_ids=[])
                      for i, (number, subject, context) in enumerate([
                          ("1", "Recipe ingredients", "The post lists this recipe's ingredients."),
                          ("1.1", "Cooking fats", "Butter appears in the ingredient list."),
                          ("1.1.1", "Butter", "Butter is explicitly listed."),
                          ("2", "Rice", "Rice is explicitly listed.")])],
            edges=[[0, 1], [1, 2]])
        self.source_path = self.root / "inputs.json"
        self.selection_path = self.root / "selection.json"
        self.source_path.write_text(json.dumps(self.source))
        self.template = (Path(__file__).parent / "bounded-hierarchy-v1" / "BCPv5.md").read_text()
        self.selection = dict(schema_version=1, inputs="inputs.json",
                              original_sp_edges=[[0, 1], [1, 2]])

    def prepare(self):
        self.selection_path.write_text(json.dumps(self.selection))
        return inputs.prepare_file(dict(adapter="bounded_comparisons"),
                                   self.selection_path, self.template)

    def test_original_entries_are_batched_without_global_remapping_or_link_hints(self):
        original = self.source_path.read_bytes()
        cases, protected, preparation = self.prepare()
        self.assertEqual(len(cases), 1)
        payload = json.loads(cases[0]["inputs"]["INPUT_JSON"])
        self.assertEqual(set(payload), {"nodes", "pairs"})
        self.assertEqual([(p["A"], p["B"]) for p in payload["pairs"]],
                         [("S0000", "S0001"), ("S0001", "S0002")])
        self.assertEqual(payload["nodes"], [dict(id=f"S{i:04d}", entries=[
            {k: self.source["subjects"][i][k] for k in ("index", "subject", "context")}])
            for i in range(3)])
        self.assertIn("original_sp_edges", preparation)
        self.assertEqual(preparation["original_sp_edges"], [[0, 1], [1, 2]])
        self.assertEqual(protected[str(self.source_path)], hashlib.sha256(original).hexdigest())
        self.assertEqual(self.source_path.read_bytes(), original)
        self.assertNotIn("expected", cases[0]["prompt"])
        value = dict(comparisons=[dict(id=p["id"], relation="neither", reason="Different scopes.")
                                 for p in payload["pairs"]])
        validated = inputs.validate(dict(adapter="bounded_comparisons"), cases[0],
                                    json.dumps(value), None)
        self.assertEqual(validated["parsed"], value)
        with self.assertRaisesRegex(ValueError, "exactly once"):
            inputs.validate(dict(adapter="bounded_comparisons"), cases[0],
                            json.dumps(dict(comparisons=[])), None)

    def test_non_source_duplicate_reversed_and_malformed_edges_are_rejected(self):
        for edges in ([[0, 3]], [[1, 0]], [[0, 1], [0, 1]], [[0, 0]],
                      [[False, 1]], [[0, 9]], [[0]], []):
            with self.subTest(edges=edges), self.assertRaises(ValueError):
                self.selection["original_sp_edges"] = edges
                self.prepare()

    def test_original_links_cannot_be_mixed_with_discovery_or_global_sources(self):
        for extra in (dict(discoveries=["some-experiment"]), dict(hierarchy="global.json")):
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                self.selection = dict(schema_version=1, inputs="inputs.json",
                                      original_sp_edges=[[0, 1]], **extra)
                self.prepare()

    def test_all_source_links_use_existing_sixteen_pair_and_token_limits(self):
        self.source["subjects"] = [dict(index=i, number=str(i + 1),
            subject=f"Subject {i}", context="Saved original context.",
            note_id="p1", note_short_id="N001") for i in range(20)]
        self.source["edges"] = [[0, i] for i in range(1, 20)]
        self.source_path.write_text(json.dumps(self.source))
        self.selection["original_sp_edges"] = "all"
        cases, _, preparation = self.prepare()
        self.assertEqual([len(json.loads(c["inputs"]["INPUT_JSON"])["pairs"]) for c in cases], [16, 3])
        self.assertEqual(len(preparation["original_sp_edges"]), 19)
        self.assertTrue(all(c["evidence"]["input_tokens"] <= 4000 for c in cases))

    def test_hash_pinned_input_rejects_changes_and_invalid_hashes(self):
        measured = hashlib.sha256(self.source_path.read_bytes()).hexdigest()
        self.selection["inputs"] = dict(path="inputs.json", sha256=measured)
        self.prepare()
        for bad_hash in (None, "wrong", 4):
            with self.subTest(hash=bad_hash), self.assertRaises(ValueError):
                self.selection["inputs"]["sha256"] = bad_hash
                self.prepare()
        self.selection["inputs"]["sha256"] = measured
        self.source_path.write_text(json.dumps({**self.source, "changed": True}))
        with self.assertRaisesRegex(ValueError, "protected source changed"):
            self.prepare()

    def test_link_endpoints_must_come_from_the_same_original_post(self):
        self.source["posts"].append(dict(note_id="p2", note_short_id="N002", text="Butter."))
        self.source["subjects"][1].update(note_id="p2", note_short_id="N002")
        self.source_path.write_text(json.dumps(self.source))
        with self.assertRaises(ValueError):
            self.prepare()

    def test_cli_prepares_one_case_without_model_calls_or_source_changes(self):
        from sse_multivector.bounded_hierarchy_workflow import COMPARISON_SCHEMA
        self.selection_path.write_text(json.dumps(self.selection))
        template_path = self.root / "BCPv5.md"
        template_path.write_text(self.template)
        spec = dict(schema_version=1, prompt=dict(id="BCPv5", path=str(template_path)),
            dataset=dict(adapter="bounded_comparisons", path=str(self.selection_path)),
            runner=dict(provider="openai-codex", auth_file=None, model="gpt-6.1-sol",
                reasoning_effort="low", concurrency=1, timeout_seconds=600,
                output_schema=COMPARISON_SCHEMA))
        spec_path = self.root / "spec.json"
        spec_path.write_text(json.dumps(spec))
        destination = self.root / "experiment"
        result = subprocess.run([sys.executable, "-m", "sse_multivector.experiment",
            "prepare", str(destination), "--spec", str(spec_path)],
            cwd=Path(__file__).resolve().parents[1], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Model calls made: 0", result.stdout)
        frozen = json.loads((destination / "experiment.json").read_text())["plan"]
        self.assertEqual(frozen["preparation"]["source_mode"], "original_sp_edges")
        self.assertEqual(len(frozen["cases"]), 1)
        self.assertFalse((destination / "run" / "results.jsonl").exists())
        report = json.loads((destination / "report.json").read_text())
        sizing = report["prepared_inputs"]
        count = frozen["cases"][0]["evidence"]["input_tokens"]
        self.assertEqual(sizing, dict(tokenizer="o200k_base", batches=1, comparisons=2,
            rendered_input_tokens=count, min_rendered_input_tokens=count,
            max_rendered_input_tokens=count))
        self.assertEqual(report["usage"]["input_tokens"], 0)
        self.assertIn("Offline input sizing", result.stdout)
        from sse_multivector.experiment import report as inspect_report
        self.assertEqual(inspect_report(destination, only=["BCPv5-0001"])["prepared_inputs"], sizing)
        empty = inspect_report(destination, only=[])["prepared_inputs"]
        self.assertEqual(empty, dict(tokenizer="o200k_base", batches=0, comparisons=0,
            rendered_input_tokens=0, min_rendered_input_tokens=0, max_rendered_input_tokens=0))


if __name__ == "__main__":
    unittest.main()
