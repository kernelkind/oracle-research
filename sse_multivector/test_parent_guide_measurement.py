"""Query-only parent-guide preparation uses original evidence and shared sizing."""

import json
import io
from contextlib import redirect_stdout
from pathlib import Path
import unittest
from unittest.mock import patch


class ParentGuideTests(unittest.TestCase):
    def fixture(self):
        from sse_multivector.test_root_candidate_measurement import RootCandidateTests
        return RootCandidateTests().fixture()[:2]

    def saved_fixture(self):
        from sse_multivector.test_root_candidate_measurement import RootCandidateTests
        root, directory, plan = RootCandidateTests.saved_build(self)
        prompt = root / "PCPv3.md"
        prompt.write_text("Suggest broader subjects.\n<input>\n{INPUT_JSON}\n</input>")
        return root, directory, plan, prompt

    def test_query_only_requests_keep_original_references_and_split(self):
        from sse_multivector.parent_guide_measurement import pack_parent_guide_requests
        from sse_multivector.test_root_candidate_measurement import RootCandidateTests

        inputs, hierarchy, _ = RootCandidateTests().fixture()
        cases = pack_parent_guide_requests(inputs, hierarchy, "Compare {INPUT_JSON}", max_queries=2)
        self.assertEqual([c["id"] for c in cases], ["PCPv3-N001-001", "PCPv3-N001-002"])
        self.assertEqual([q for c in cases for q in c["evidence"]["queries"]],
                         ["S0000", "S0001", "S0002", "S0003"])
        payload = json.loads(cases[0]["inputs"]["INPUT_JSON"])
        self.assertEqual(set(payload), {"queries"})
        self.assertEqual(payload["queries"][0], dict(id="S0000", entries=[
            dict(index=0, subject="Beverages", context="Beverages")]))

    def test_merged_node_is_owned_once_and_keeps_two_original_references(self):
        from sse_multivector.parent_guide_measurement import pack_parent_guide_requests

        inputs, _ = self.fixture()
        inputs["subjects"][1].update(note_id="N002", note_short_id="N002")
        hierarchy = dict(groups=[[0, 1], [2], [3]], edges=[])
        cases = pack_parent_guide_requests(inputs, hierarchy, "Compare {INPUT_JSON}")
        self.assertEqual([q for c in cases for q in c["evidence"]["queries"]],
                         ["S0000", "S0002", "S0003"])
        evidence = cases[0]["evidence"]
        self.assertEqual(evidence["source_post"], "N001")
        self.assertEqual(evidence["original_members"]["S0000"], [0, 1])
        self.assertEqual(evidence["query_entries"]["S0000"], [
            dict(index=i, subject=inputs["subjects"][i]["subject"],
                 context=inputs["subjects"][i]["context"]) for i in [0, 1]])

    def test_actual_rendered_tokens_split_and_oversized_single_query_fails_closed(self):
        import tiktoken
        from sse_multivector.parent_guide_measurement import pack_parent_guide_requests
        from sse_multivector.experiment_inputs import render

        inputs, hierarchy = self.fixture()
        template = 'Literal JSON: {"parents": []}\nCompare {INPUT_JSON}'
        singles = pack_parent_guide_requests(inputs, hierarchy, template, max_queries=1)
        limit = max(c["evidence"]["input_tokens"] for c in singles)
        cases = pack_parent_guide_requests(inputs, hierarchy, template, max_input_tokens=limit)
        self.assertEqual(len(cases), 4)
        encoding = tiktoken.get_encoding("o200k_base")
        for case in cases:
            self.assertEqual(case["evidence"]["input_tokens"],
                             len(encoding.encode(render(template, case["inputs"]))))
        with self.assertRaisesRegex(ValueError, "S0000 exceeds"):
            pack_parent_guide_requests(inputs, hierarchy, template, max_input_tokens=1)

    def test_large_source_and_invalid_limits_are_refused_before_graph_preparation(self):
        from sse_multivector import parent_guide_measurement as measurement

        inputs, hierarchy = self.fixture()
        for limits in [dict(max_queries=17), dict(max_queries=True), dict(max_input_tokens=4001)]:
            with self.subTest(limits=limits), self.assertRaises(ValueError):
                measurement.pack_parent_guide_requests(inputs, hierarchy, "{INPUT_JSON}", **limits)
        inputs["subjects"] *= 1251
        with patch.object(measurement, "_validate_graph", side_effect=AssertionError("graph reached")) as graph:
            with self.assertRaisesRegex(ValueError, "limited to 5000"):
                measurement.pack_parent_guide_requests(inputs, hierarchy, "{INPUT_JSON}")
            graph.assert_not_called()

    def test_draft_schema_bounds_distinct_parent_names(self):
        from sse_multivector.parent_guide_measurement import PARENT_GUIDE_SCHEMA

        parents = PARENT_GUIDE_SCHEMA["properties"]["queries"]["items"]["properties"]["parents"]
        self.assertEqual(parents["maxItems"], 3)
        self.assertEqual(parents["items"]["maxLength"], 160)
        self.assertTrue(parents["uniqueItems"])

    def test_real_cli_measures_one_pass_without_jobs_vectors_or_source_changes(self):
        from sse_multivector import experiment
        from sse_multivector import subject_matching_probe

        root, directory, plan, prompt = self.saved_fixture()
        before = {p: p.read_bytes() for p in directory.rglob("*") if p.is_file()}
        output = io.StringIO()
        destination = root / "measurement"
        with patch.object(experiment, "run", side_effect=AssertionError("inference reached")), \
                patch.object(subject_matching_probe, "load_subject_vectors",
                             side_effect=AssertionError("vectors reached")), redirect_stdout(output):
            self.assertEqual(experiment.main(["measure-parent-guides", str(directory), str(destination),
                                              "--prompt", str(prompt), "--prompt-id", "PCPv3"]), 0)
        result = json.loads((destination / "report.json").read_text())
        self.assertEqual(result["inference_attempts"], 0)
        self.assertEqual(result["new_vectors"], 0)
        self.assertEqual(result["supplementary_passes"], 1)
        self.assertEqual(result["maximum_parent_guides"], 12)
        self.assertEqual(result["maximum_unique_resolved_pairs"], 6)
        self.assertEqual(result["prospective_sse_encodings_upper"], 12)
        self.assertEqual(result["comparison_capacity"]["proof"]["universe"],
                         "any_two_distinct_supplied_nodes")
        self.assertEqual(result["maximum_first_attempt_requests"],
                         result["discovery_requests"] + result["maximum_verification_requests"])
        self.assertEqual(result["maximum_attempts_with_one_retry"],
                         2 * result["maximum_first_attempt_requests"])
        self.assertEqual(result["remaining_attempts"], 2000)
        self.assertTrue(result["requires_new_versioned_pass_authorization"])
        self.assertTrue(result["existing_quota_unchanged"])
        self.assertIsNone(result["output_and_reasoning_token_ceiling"])
        self.assertEqual(result["source_runner"], plan["spec"]["runner"])
        self.assertTrue({"bounded_hierarchy_build.py", "experiment_inputs.py", "extraction_pipeline.py"}
                        <= {Path(p).name for p in result["code_sha256"]})
        requirements = Path(__file__).with_name("bounded-hierarchy-v1") / "requirements.txt"
        self.assertIn(str(requirements.resolve()), result["protected_sha256"])
        self.assertTrue(result["tokenizer_library_version"])
        self.assertEqual(json.loads(output.getvalue())["model_settings"],
                         dict(provider="openai-codex", model="gpt-6.1-sol", reasoning_effort="low"))
        self.assertEqual({p: p.read_bytes() for p in before}, before)
        self.assertFalse((destination / "experiment.json").exists())
        self.assertEqual((destination / ".gitignore").read_text(), "*\n")

    def test_saved_budget_source_and_export_hashes_fail_before_packing(self):
        from sse_multivector import parent_guide_measurement as measurement

        root, directory, plan, prompt = self.saved_fixture()
        paths = [directory / "bounded-build.json", directory / "budget.json",
                 Path(plan["spec"]["inputs"]), Path(plan["export"]) / "results.json"]
        for path in paths:
            original = path.read_bytes()
            if path.name == "budget.json":
                path.write_text(json.dumps(dict(schema_version=1, limit=2001, used=0)))
            elif path.name == "bounded-build.json":
                envelope = json.loads(original)
                envelope["sha256"] = "wrong"
                path.write_text(json.dumps(envelope))
            else:
                path.write_bytes(original + b"\n")
            try:
                with self.subTest(path=path.name), patch.object(measurement, "pack_parent_guide_requests",
                        side_effect=AssertionError("packing reached")) as packer:
                    with self.assertRaises(ValueError):
                        measurement.measure_build(directory, root / "measurement", prompt=prompt)
                    packer.assert_not_called()
                self.assertFalse((root / "measurement").exists())
            finally:
                path.write_bytes(original)


if __name__ == "__main__":
    unittest.main()
