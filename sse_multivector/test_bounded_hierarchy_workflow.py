"""Offline tests of bounded discovery and comparison production preparation."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from sse_multivector import bounded_hierarchy_workflow as workflow


def discovery_case():
    payload = {
        "queries": [{"id": "S0000", "entries": [
            {"index": 0, "subject": "Tea", "context": "The writer drinks tea."}]}],
        "candidates": [{"id": "S0001", "subjects": ["Beverages"]},
                       {"id": "S0002", "subjects": ["Tea drinking"]}],
        "excluded_candidates": {"S0000": ["S0002"]},
    }
    return {"id": "PCPv2-N001-001", "inputs": {
        "INPUT_JSON": json.dumps(payload)}, "evidence": {
            "queries": ["S0000"], "candidates": ["S0001", "S0002"],
            "query_entries": {"S0000": payload["queries"][0]["entries"]},
            "candidate_wordings": {c["id"]: c["subjects"] for c in payload["candidates"]},
            "excluded_candidates": payload["excluded_candidates"],
            "source_post": "N001"}}


class BoundedHierarchyWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.inputs = dict(posts=[dict(note_id="p1", text="Tea."),
                                  dict(note_id="p2", text="Coffee.")],
            subjects=[dict(index=i, subject=subject, context=context,
                           note_id="p1" if i < 2 else "p2",
                           note_short_id="N001" if i < 2 else "N002")
                      for i, (subject, context) in enumerate([
                          ("Tea", "The writer drinks tea."),
                          ("Beverages", "The writer names drinks."),
                          ("Tea", "Tea is served."),
                          ("Tea drinking", "The writer discusses drinking tea."),
                          ("Tea", "The writer drinks tea."),
                          ("Coffee", "The writer drinks coffee.")])],
            edges=[[1, 0]])
        self.hierarchy = dict(groups=[[0, 2, 3, 4], [1], [5]],
                              member_to_group=[0, 1, 0, 0, 0, 2], edges=[[1, 0]])
        self.refs, self.references = dict(schema_version=1), {}
        for name, value in (("inputs", self.inputs), ("hierarchy", self.hierarchy)):
            path = self.root / (name + ".json")
            path.write_text(json.dumps(value))
            self.refs[name] = str(path)
            self.references[name] = dict(path=str(path),
                sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        self.template = (Path(__file__).parent / "bounded-hierarchy-v1" / "BCPv5.md").read_text()

    def report(self, reciprocal=False):
        from sse_multivector.bounded_hierarchy_candidates import compact_entries
        nodes = {"S0000": compact_entries(self.inputs, [0, 2, 3, 4]),
                 "S0005": compact_entries(self.inputs, [5])}
        cases = []
        for qid, cid in ([('S0000', 'S0005'), ('S0005', 'S0000')]
                         if reciprocal else [('S0000', 'S0005')]):
            payload = dict(queries=[dict(id=qid, entries=nodes[qid])],
                candidates=[dict(id=cid, subjects=(["Tea", "Tea drinking"]
                             if cid == "S0000" else ["Coffee"]))],
                excluded_candidates={qid: []})
            cases.append(dict(id="PCPv2-" + qid, status="valid",
                inputs=dict(INPUT_JSON=json.dumps(payload)),
                evidence=dict(source=self.references, queries=[qid]),
                parsed=dict(queries=[dict(id=qid, candidates=[dict(id=cid, reason="Check it.")])]),
                receipt=dict(results_path=str(self.root / "results.jsonl"), record_sha256="receipt")))
        (self.root / "results.jsonl").write_text("{}\n")
        (self.root / "experiment.json").write_text(json.dumps(dict(plan=dict(files={}))))
        return dict(experiment=str(self.root), prompt_id="PCPv2", settings=dict(model="fixture"),
                    cases=cases)

    def test_discovery_cannot_nominate_an_excluded_supplied_candidate(self):
        raw = json.dumps({"queries": [{"id": "S0000", "candidates": [
            {"id": "S0002", "reason": "Tea drinking might be related."}]}]})
        with self.assertRaisesRegex(ValueError, "excluded"):
            workflow.validate_discovery(discovery_case(), raw)

    def test_discovery_may_nominate_nothing(self):
        value = {"queries": [{"id": "S0000", "candidates": []}]}
        self.assertEqual(workflow.validate_discovery(discovery_case(), json.dumps(value)), value)

    def test_discovery_rejects_missing_duplicate_unknown_and_overquota_queries(self):
        case = discovery_case()
        for value in ({"queries": []},
                      {"queries": [{"id": "unknown", "candidates": []}]},
                      {"queries": [{"id": "S0000", "candidates": []}] * 2},
                      {"queries": [{"id": "S0000", "candidates": [
                          {"id": "S0001", "reason": "Check it."}] * 4}]},
                      {"queries": [{"id": "S0000", "candidates": [
                          {"id": "S0001", "reason": " "}]}]}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                workflow.validate_discovery(case, json.dumps(value))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            workflow.validate_discovery(case, '{"queries":[],"queries":[]}')

    def test_reciprocal_nominations_share_one_pair_and_keep_both_proofs(self):
        cases, protected, preparation = workflow.build_comparison_source(
            self.refs, [self.report(reciprocal=True)], self.template)
        self.assertEqual(len(cases), 1)
        self.assertEqual(len(preparation["pairs"]), 1)
        pair = preparation["pairs"][0]
        self.assertEqual((pair["id"], pair["A"], pair["B"]),
                         ("S0000-S0005", "S0000", "S0005"))
        self.assertEqual(len(pair["parent_candidates"]), 2)
        self.assertEqual([e["index"] for e in pair["reference_entries"]["A"]], [0, 3])
        self.assertIn(str(self.root / "results.jsonl"), protected)
        self.assertLessEqual(cases[0]["evidence"]["input_tokens"], 4000)
        value = {"comparisons": [{"id": pair["id"], "relation": "neither", "reason": "Neither contains the other."}]}
        rows = workflow.extract_comparisons(cases[0], value)
        self.assertEqual(rows[0]["answer"], {"relation": "neither", "reason": "Neither contains the other."})
        self.assertEqual(rows[0]["reference_entries"], pair["reference_entries"])
        self.assertEqual(len(rows[0]["parent_candidates"]), 2)

    def test_comparison_cases_use_the_shared_generic_preparation_codepath(self):
        from sse_multivector.experiment_inputs import prepare
        cases, _, _ = workflow.build_comparison_source(self.refs, [self.report()], self.template)
        prepared = prepare({"adapter": "generic"}, {"cases": cases}, self.template)
        self.assertEqual(len(prepared), 1)
        self.assertIn("Compare the subjects", prepared[0]["prompt"])

    def test_failed_discovery_is_explicitly_unresolved_without_guessed_pairs(self):
        report = self.report()
        report["cases"][0].update(status="failed", parsed=None)
        with self.assertRaisesRegex(ValueError, "complete valid"):
            workflow.build_comparison_source(self.refs, [report], self.template)
        cases, _, preparation = workflow.build_comparison_source(
            self.refs, [report], self.template, allow_incomplete=True)
        self.assertEqual(cases, [])
        self.assertEqual(preparation["pairs"], [])
        self.assertEqual(preparation["unresolved_discovery"][0]["queries"], ["S0000"])

    def test_comparison_requires_exact_pair_inventory_and_valid_relations(self):
        cases, _, _ = workflow.build_comparison_source(self.refs, [self.report()], self.template)
        case = cases[0]
        row = dict(id="S0000-S0005", relation="uncertain", reason="The references leave meaning unresolved.")
        self.assertEqual(workflow.validate_comparisons(case, json.dumps({"comparisons": [row]}))["comparisons"], [row])
        for value in ({"comparisons": []}, {"comparisons": [row, row]},
                      {"comparisons": [{**row, "id": "unknown"}]},
                      {"comparisons": [{**row, "relation": "related"}]},
                      {"comparisons": [{**row, "reason": " "}]}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                workflow.validate_comparisons(case, json.dumps(value))

    def test_oversize_single_pair_fails_instead_of_truncating_original_references(self):
        with self.assertRaisesRegex(ValueError, "single comparison exceeds"):
            workflow.build_comparison_source(self.refs, [self.report()], self.template,
                                             max_input_tokens=10)

    def test_actual_rendered_tokens_and_sixteen_pair_limit_split_large_workloads(self):
        count = 40
        self.inputs["subjects"] = [dict(index=i, subject=f"Subject {i}",
            context="Original evidence " * 250, note_id="p1", note_short_id="N001")
            for i in range(count)]
        self.inputs["edges"] = []
        self.hierarchy = dict(groups=[[i] for i in range(count)],
                              member_to_group=list(range(count)), edges=[])
        for name, value in (("inputs", self.inputs), ("hierarchy", self.hierarchy)):
            path = self.root / (name + ".json")
            path.write_text(json.dumps(value))
            self.references[name]["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        report = self.report()
        payload = dict(queries=[dict(id=f"S{i:04d}", entries=[dict(index=i,
            subject=f"Subject {i}", context="Original evidence " * 250)]) for i in range(20)],
            candidates=[dict(id=f"S{i:04d}", subjects=[f"Subject {i}"])
                        for i in range(20, count)],
            excluded_candidates={f"S{i:04d}": [] for i in range(20)})
        report["cases"][0]["inputs"]["INPUT_JSON"] = json.dumps(payload)
        report["cases"][0]["parsed"] = dict(queries=[dict(id=f"S{i:04d}", candidates=[
            dict(id=f"S{20 + (i + offset) % 20:04d}", reason="Check it.") for offset in range(3)])
            for i in range(20)])
        cases, _, preparation = workflow.build_comparison_source(self.refs, [report], self.template)
        self.assertEqual(len(preparation["pairs"]), 60)
        self.assertGreater(len(cases), 4)  # The token budget, not just 16 pairs, forces splits.
        import tiktoken
        encoding = tiktoken.get_encoding("o200k_base")
        for case in cases:
            from sse_multivector.experiment_inputs import render
            prompt = render(self.template, case["inputs"])
            payload = json.loads(case["inputs"]["INPUT_JSON"])
            self.assertLessEqual(len(payload["pairs"]), 16)
            self.assertLessEqual(len(encoding.encode(prompt)), 4000)
            self.assertEqual(case["evidence"]["input_tokens"], len(encoding.encode(prompt)))
            self.assertTrue(all(len(node["entries"]) == 1 for node in payload["nodes"]))

    def test_incomplete_mode_discards_a_whole_malformed_case_not_some_nominations(self):
        report = self.report()
        report["cases"][0]["parsed"]["queries"][0]["candidates"].append(
            dict(id="unknown", reason="Malformed nomination."))
        cases, _, preparation = workflow.build_comparison_source(
            self.refs, [report], self.template, allow_incomplete=True)
        self.assertEqual(cases, [])
        self.assertEqual(preparation["unresolved_discovery"][0]["status"], "malformed")

    def test_discovery_saved_source_hashes_are_revalidated(self):
        report = self.report()
        source = self.root / "saved-vector-reference.json"
        source.write_text("original")
        (self.root / "experiment.json").write_text(json.dumps(dict(plan=dict(files={},
            sources={str(source): hashlib.sha256(b"original").hexdigest()}))))
        source.write_text("changed")
        with self.assertRaisesRegex(ValueError, "protected discovery source changed"):
            workflow.build_comparison_source(self.refs, [report], self.template)

    def test_changed_source_reference_is_rejected(self):
        self.refs["inputs"] = self.references["inputs"]
        (self.root / "inputs.json").write_text("{}")
        with self.assertRaisesRegex(ValueError, "protected source changed"):
            workflow.build_comparison_source(self.refs, [self.report()], self.template)

    def test_workflow_module_imports_in_the_supported_direct_script_environment(self):
        result = subprocess.run([sys.executable, "-c", "import bounded_hierarchy_workflow"],
                                cwd=Path(__file__).parent, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_bcpv5_preserves_the_existing_five_relation_definitions(self):
        original = (Path(__file__).parent / "branch-comparison-prompt-v1" / "BCPv4.md").read_text()
        before = [line for line in original.splitlines() if line.startswith("- ")]
        after = [line for line in self.template.splitlines() if line.startswith("- ")]
        self.assertEqual(before, after)

    def test_first_original_entry_fixes_scope_and_second_cannot_redefine_it(self):
        self.assertIn("The first entry fixes the subject being compared.", self.template)
        self.assertIn("it must not redefine the subject", self.template)
        self.assertIn("If the entries conflict", self.template)
        discovery = (Path(__file__).parent / "bounded-hierarchy-v1" / "PCPv2.md").read_text()
        self.assertIn("The first entry fixes the query subject", discovery)
        self.assertIn("must not redefine", discovery)

    def test_shared_output_schemas_match_the_production_validators(self):
        self.assertEqual(workflow.DISCOVERY_SCHEMA["required"], ["queries"])
        query = workflow.DISCOVERY_SCHEMA["properties"]["queries"]["items"]
        self.assertEqual(query["properties"]["candidates"]["maxItems"], 3)
        comparison = workflow.COMPARISON_SCHEMA["properties"]["comparisons"]["items"]
        self.assertEqual(comparison["properties"]["relation"]["enum"], list(workflow.RELATIONS))
        self.assertEqual(comparison["required"], ["id", "relation", "reason"])

    def test_unknown_retrieval_backend_is_rejected_before_reading_vector_sources(self):
        refs = {**self.refs, "retrieval_backend": "unknown", "subject_probe": "missing"}
        with self.assertRaisesRegex(ValueError, "retrieval_backend"):
            workflow.create_discovery_source(refs, "{INPUT_JSON}")


if __name__ == "__main__":
    unittest.main()
