"""The small parent-guide experiment uses shared preparation and validators."""

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from sse_multivector import experiment_inputs


class ParentGuideWorkflowTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        names = ["Butter", "Dairy products", "Fats", "Food", "Community", "Social media"]
        self.inputs = dict(posts=[dict(note_id=f"p{i}", text=name) for i, name in enumerate(names)],
            subjects=[dict(index=i, subject=name, context=f"The post discusses {name}.",
                           note_id=f"p{i}", note_short_id=f"N{i + 1:03d}")
                      for i, name in enumerate(names)], edges=[])
        self.hierarchy = dict(groups=[[i] for i in range(len(names))],
            member_to_group=list(range(len(names))), edges=[[3, 1], [3, 2]])
        self.refs = dict(schema_version=1)
        for name, value in (("inputs", self.inputs), ("hierarchy", self.hierarchy)):
            path = self.root / (name + ".json")
            path.write_text(json.dumps(value))
            self.refs[name] = dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        self.source_path = self.root / "source.json"
        self.template = "Suggest parent names. {INPUT_JSON}"

    def prepare_guides(self, **changes):
        self.source_path.write_text(json.dumps(dict(self.refs, **changes)))
        return experiment_inputs.prepare_file(dict(adapter="bounded_parent_guides"),
                                               self.source_path, self.template)

    def save_sources(self):
        for name, value in (("inputs", self.inputs), ("hierarchy", self.hierarchy)):
            path = Path(self.refs[name]["path"])
            path.write_text(json.dumps(value))
            self.refs[name]["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()

    def add_aliases(self, count):
        for i in range(6, 6 + count):
            self.inputs["posts"].append(dict(note_id=f"p{i}", text="Dairy products"))
            self.inputs["subjects"].append(dict(index=i, subject="Dairy products", context=f"Dairy {i}.",
                                                note_id=f"p{i}", note_short_id=f"N{i + 1:03d}"))
            self.hierarchy["groups"].append([i])
            self.hierarchy["member_to_group"].append(i)
        self.save_sources()

    def test_shared_adapter_selects_current_queries_without_a_catalogue(self):
        cases, protected, preparation = self.prepare_guides(query_nodes=["S0000", "S0005"])
        self.assertEqual([q for c in cases for q in c["evidence"]["queries"]], ["S0000", "S0005"])
        self.assertEqual([c["id"] for c in cases], ["PCPv3-N001-001", "PCPv3-N006-001"])
        self.assertTrue(all(set(json.loads(c["inputs"]["INPUT_JSON"])) == {"queries"} for c in cases))
        self.assertEqual(cases[0]["evidence"]["query_entries"]["S0000"], [
            dict(index=0, subject="Butter", context="The post discusses Butter.")])
        self.assertEqual(preparation["phase"], "parent_guides")
        self.assertIn(self.refs["inputs"]["path"], protected)

    def test_validator_requires_ordered_complete_queries_and_bounded_distinct_names(self):
        case = self.prepare_guides()[0][0]
        answer = dict(queries=[dict(id="S0000", parents=["Dairy products", "食べ物"])])
        dataset = dict(adapter="bounded_parent_guides")
        self.assertEqual(experiment_inputs.validate(dataset, case, json.dumps(answer), None)["parsed"], answer)
        for parents in (["Dairy products"] * 2, ["a"] * 4, [" "], ["a" * 161], [7], {}):
            with self.subTest(parents=parents), self.assertRaises(ValueError):
                experiment_inputs.validate(dataset, case, json.dumps(dict(queries=[
                    dict(id="S0000", parents=parents)])), None)
        for queries in ([], [answer["queries"][0]] * 2, [dict(id="S0005", parents=[])],
                        [dict(id="S0000", parents=[], reason="extra")]):
            with self.subTest(queries=queries), self.assertRaises(ValueError):
                experiment_inputs.validate(dataset, case, json.dumps(dict(queries=queries)), None)
        with self.assertRaisesRegex(ValueError, "duplicate"):
            experiment_inputs.validate(dataset, case, '{"queries":[],"queries":[]}', None)
        second = self.prepare_guides()[0][1]
        payload = json.loads(case["inputs"]["INPUT_JSON"])
        payload["queries"] += json.loads(second["inputs"]["INPUT_JSON"])["queries"]
        case["inputs"]["INPUT_JSON"] = json.dumps(payload)
        with self.assertRaisesRegex(ValueError, "order"):
            experiment_inputs.validate(dataset, case, json.dumps(dict(queries=[
                dict(id="S0001", parents=[]), dict(id="S0000", parents=[])])), None)

    def test_invalid_query_subset_and_foreign_refs_are_rejected(self):
        for ids in ([], ["S0000"] * 2, ["S9999"], [True], "S0000"):
            with self.subTest(ids=ids), self.assertRaises(ValueError):
                self.prepare_guides(query_nodes=ids)
        with self.assertRaisesRegex(ValueError, "invalid parent-guide"):
            self.prepare_guides(subject_probe="unused")
        from sse_multivector.parent_guide_measurement import pack_parent_guide_requests
        default = pack_parent_guide_requests(self.inputs, self.hierarchy, self.template)
        explicit = pack_parent_guide_requests(self.inputs, self.hierarchy, self.template,
                                            query_nodes=[f"S{i:04d}" for i in range(6)])
        self.assertEqual(default, explicit)

    def guide_report(self, proposals):
        cases = self.prepare_guides(query_nodes=list(proposals))[0]
        directory = self.root / "guides"
        directory.mkdir(exist_ok=True)
        receipt = directory / "results.jsonl"
        receipt.write_text("{}\n")
        (directory / "experiment.json").write_text(json.dumps(dict(plan=dict(files={}, sources={}))))
        for case in cases:
            case.update(status="valid", parsed=dict(queries=[dict(id=q, parents=proposals[q])
                for q in case["evidence"]["queries"]]),
                receipt=dict(results_path=str(receipt), record_sha256="fixture"))
        return dict(adapter="bounded_parent_guides", prompt_id="PCPv3", experiment=str(directory),
                    settings=dict(model="fixture"), cases=cases)

    def prepare_comparisons(self, report, **changes):
        comparison_source = self.root / "comparisons.json"
        comparison_source.write_text(json.dumps(dict(self.refs, discoveries=[report["experiment"]], **changes)))
        template = (Path(__file__).parent / "bounded-hierarchy-v1" / "BCPv5.md").read_text()
        return experiment_inputs.prepare_file(dict(adapter="bounded_parent_comparisons"),
            comparison_source, template, load_report=lambda path: report)

    def test_exact_names_produce_real_pairs_and_missing_names_remain_unresolved(self):
        report = self.guide_report({"S0000": ["Dairy products", "Fats", "Imagined parent"],
                                    "S0005": ["Community", "Butter"]})
        cases, protected, preparation = self.prepare_comparisons(report)
        self.assertEqual([(p["A"], p["B"]) for p in preparation["pairs"]],
                         [("S0000", "S0001"), ("S0000", "S0002"),
                          ("S0000", "S0005"), ("S0004", "S0005")])
        self.assertEqual(preparation["unresolved_guides"][0]["name"], "Imagined parent")
        self.assertEqual(preparation["unresolved_guides"][0]["reason"], "exact_name_absent")
        self.assertEqual(len(cases), 1)
        payload = json.loads(cases[0]["inputs"]["INPUT_JSON"])
        self.assertEqual(payload["nodes"][0]["entries"], [
            dict(index=0, subject="Butter", context="The post discusses Butter.")])
        self.assertIn(str(Path(report["experiment"]) / "results.jsonl"), protected)
        rows = dict(comparisons=[dict(id=p["id"], relation="uncertain", reason="Unresolved meaning.")
                                  for p in preparation["pairs"]])
        parsed = experiment_inputs.validate(dict(adapter="bounded_parent_comparisons"), cases[0],
                                             json.dumps(rows), None)["parsed"]
        self.assertEqual(parsed, rows)

    def test_ambiguous_names_keep_three_total_candidates_not_three_per_name(self):
        self.add_aliases(4)
        report = self.guide_report({"S0000": ["Dairy products", "Fats", "Community"]})
        _, _, preparation = self.prepare_comparisons(report)
        self.assertEqual(preparation["candidates_by_query"]["S0000"], ["S0001", "S0006", "S0007"])
        self.assertEqual(len(preparation["pairs"]), 3)
        self.assertEqual([g["reason"] for g in preparation["skipped_guides"]],
                         ["candidate_limit", "candidate_limit"])
        self.assertFalse(preparation["guides"][0]["search_complete"])

    def test_alias_budget_is_shared_across_names_and_exhaustion_is_not_absence(self):
        from sse_multivector.bounded_hierarchy_workflow import _node_entries
        self.add_aliases(30)
        nodes = _node_entries(self.inputs, self.hierarchy)
        judgments = [dict(A="S0000", B=nid, reference_entries=dict(A=nodes["S0000"], B=entries))
                     for nid, entries in nodes.items() if entries[0]["subject"] == "Dairy products"]
        path = self.root / "judgments.json"
        path.write_text(json.dumps(dict(subjects=self.inputs["subjects"], comparisons=judgments)))
        report = self.guide_report({"S0000": ["Dairy products", "Fats", "Community"]})
        _, _, preparation = self.prepare_comparisons(report, judgments=str(path))
        self.assertEqual(preparation["alias_inspections_by_query"]["S0000"], 32)
        self.assertEqual(preparation["candidates_by_query"]["S0000"], ["S0002"])
        self.assertEqual(preparation["skipped_guides"][0]["name"], "Community")
        self.assertEqual(preparation["skipped_guides"][0]["reason"], "alias_limit")
        self.assertEqual(preparation["unresolved_guides"][0]["reason"], "no_eligible_exact_match")

    def test_bounded_build_history_excludes_only_unchanged_reference_pairs(self):
        from sse_multivector.bounded_hierarchy_workflow import _node_entries
        entries = _node_entries(self.inputs, self.hierarchy)
        comparison = dict(A="S0000", B="S0001", reference_entries=dict(A=entries["S0000"], B=entries["S0001"]))
        plan = dict(spec=dict(inputs=self.refs["inputs"]["path"]),
                    protected_sha256={self.refs["inputs"]["path"]: self.refs["inputs"]["sha256"]},
                    comparisons=[comparison])
        path = self.root / "bounded-build.json"
        path.write_text(json.dumps(dict(plan=plan, sha256=experiment_inputs.digest(plan))))
        report = self.guide_report({"S0000": ["Dairy products", "Fats"]})
        _, _, preparation = self.prepare_comparisons(report, judgments=str(path))
        self.assertEqual(len(preparation["pairs"]), 1)
        self.assertEqual(preparation["guides"][0]["skipped_nodes"],
                         [dict(id="S0001", reason="unchanged_judgment")])
        self.hierarchy.update(groups=[[0, 5], [1], [2], [3], [4]], member_to_group=[0, 1, 2, 3, 4, 0])
        self.save_sources()
        report = self.guide_report({"S0000": ["Dairy products", "Fats"]})
        _, _, preparation = self.prepare_comparisons(report, judgments=str(path))
        self.assertEqual(len(preparation["pairs"]), 2)
        envelope = json.loads(path.read_text())
        envelope["sha256"] = "wrong"
        path.write_text(json.dumps(envelope))
        with self.assertRaisesRegex(ValueError, "build digest"):
            self.prepare_comparisons(report, judgments=str(path))
        plan["protected_sha256"][self.refs["inputs"]["path"]] = "wrong"
        path.write_text(json.dumps(dict(plan=plan, sha256=experiment_inputs.digest(plan))))
        with self.assertRaisesRegex(ValueError, "SP inputs differ"):
            self.prepare_comparisons(report, judgments=str(path))

    def test_unknown_ancestry_is_excluded_with_an_explicit_bounded_walk(self):
        from sse_multivector import parent_guide_workflow as workflow
        report = self.guide_report({"S0000": ["Dairy products"]})
        references = {name: self.refs[name] for name in ("inputs", "hierarchy")}
        with patch.object(workflow, "_ancestor", return_value=None) as ancestor:
            pairs, _, resolution = workflow.resolve_exact_guides(
                self.inputs, self.hierarchy, [report], references)
        self.assertEqual(pairs, [])
        self.assertEqual(resolution["guides"][0]["skipped_nodes"],
                         [dict(id="S0001", reason="ancestry_work_limit")])
        self.assertEqual(ancestor.call_count, 2)
        self.assertTrue(all(call.kwargs == dict(max_operations=2048) for call in ancestor.call_args_list))

    def test_self_and_current_ancestry_are_skipped_not_semantically_rejected(self):
        report = self.guide_report({"S0001": ["Dairy products", "Food", "Butter"]})
        _, _, preparation = self.prepare_comparisons(report)
        self.assertEqual(len(preparation["pairs"]), 1)
        self.assertEqual(preparation["guides"][0]["skipped_nodes"], [dict(id="S0001", reason="self")])
        self.assertEqual(preparation["guides"][1]["skipped_nodes"],
                         [dict(id="S0003", reason="existing_ancestry")])

    def test_saved_guide_sources_and_answers_are_revalidated_before_pair_packing(self):
        from sse_multivector import parent_guide_workflow as workflow
        for mutation in ("source", "query", "invalid", "duplicate_name"):
            report = self.guide_report({"S0000": ["Dairy products"]})
            case = report["cases"][0]
            if mutation == "source":
                case["evidence"]["source"]["inputs"]["sha256"] = "wrong"
            elif mutation == "query":
                payload = json.loads(case["inputs"]["INPUT_JSON"])
                payload["queries"][0]["entries"][0]["context"] = "changed"
                case["inputs"]["INPUT_JSON"] = json.dumps(payload)
            elif mutation == "invalid":
                case["status"] = "failed"
            else:
                case["parsed"]["queries"][0]["parents"] *= 2
            with self.subTest(mutation=mutation), patch.object(workflow.bounded, "_pack_comparisons",
                    side_effect=AssertionError("packing reached")) as packer:
                with self.assertRaises(ValueError):
                    self.prepare_comparisons(report)
                packer.assert_not_called()
        report = self.guide_report({"S0000": ["Dairy products"]})
        directory = Path(report["experiment"])
        path = directory / "prompt.txt"
        path.write_text("Original prompt")
        (directory / "experiment.json").write_text(json.dumps(dict(plan=dict(files={
            "prompt.txt": hashlib.sha256(path.read_bytes()).hexdigest()}, sources={}))))
        path.write_text("Changed prompt")
        with self.assertRaisesRegex(ValueError, "protected parent-guide source changed"):
            self.prepare_comparisons(report)

    def test_case_selection_and_comparison_reports_loader_are_required(self):
        report = self.guide_report({"S0000": ["Dairy products"]})
        self.prepare_comparisons(report)
        with self.assertRaisesRegex(ValueError, "validated experiment reports"):
            experiment_inputs.prepare_file(dict(adapter="bounded_parent_comparisons"),
                                           self.root / "comparisons.json", "{INPUT_JSON}")
        selected = experiment_inputs.prepare_file(dict(adapter="bounded_parent_guides", select=["PCPv3-N001-001"]),
                                                 self.source_path, self.template)[0]
        self.assertEqual([case["id"] for case in selected], ["PCPv3-N001-001"])

    def subject_vectors(self, extra=None):
        rows = {"Butter": [0, 1, 0], "Dairy products": [1, 0, 0],
                "Fats": [0.9, 0.1, 0], "Food": [0, 0, 1],
                "Community": [-1, 0, 0], "Social media": [0, -1, 0]}
        rows.update(extra or {})
        return {(hashlib.sha256(word.encode()).hexdigest(),
                 hashlib.sha256(word.encode()).hexdigest()[:16]): vector
                for word, vector in rows.items()}

    def test_vector_fallback_retrieves_actual_nodes_without_repeating_exact_pairs(self):
        from sse_multivector.parent_guide_workflow import resolve_vector_guides
        report = self.guide_report({"S0000": ["Dairy products", "Edible fats"]})
        references = {name: self.refs[name] for name in ("inputs", "hierarchy")}
        pairs, nodes, resolution = resolve_vector_guides(self.inputs, self.hierarchy,
            [report], references, self.subject_vectors({"Edible fats": [0.9, 0.1, 0]}))
        self.assertEqual([(p["A"], p["B"]) for p in pairs], [("S0000", "S0002")])
        self.assertEqual(pairs[0]["reference_entries"]["B"], nodes["S0002"])
        candidate = pairs[0]["parent_candidates"][0]["candidate"]
        self.assertEqual(candidate["name"], "Edible fats")
        self.assertEqual(candidate["matched_wording"], "Fats")
        self.assertAlmostEqual(candidate["cosine"], 1)
        self.assertEqual(resolution["exact_pairs_excluded_from_trial"], ["S0000-S0001"])
        self.assertEqual(resolution["candidates_by_query"]["S0000"], ["S0001", "S0002"])

    def test_vector_fallback_preserves_missing_vector_and_alias_work_limits(self):
        from sse_multivector.parent_guide_workflow import resolve_vector_guides
        from sse_multivector.bounded_hierarchy_workflow import _node_entries
        report = self.guide_report({"S0000": ["Edible fats"]})
        references = {name: self.refs[name] for name in ("inputs", "hierarchy")}
        with self.assertRaisesRegex(ValueError, "missing.*guide vector"):
            resolve_vector_guides(self.inputs, self.hierarchy, [report], references,
                                  self.subject_vectors())
        self.add_aliases(35)
        report = self.guide_report({"S0000": ["Edible fats"]})
        references = {name: self.refs[name] for name in ("inputs", "hierarchy")}
        nodes = _node_entries(self.inputs, self.hierarchy)
        history = dict(subjects=self.inputs["subjects"], comparisons=[
            dict(A="S0000", B=nid, reference_entries=dict(A=nodes["S0000"], B=entries))
            for nid, entries in nodes.items() if entries[0]["subject"] == "Dairy products"])
        pairs, _, resolution = resolve_vector_guides(self.inputs, self.hierarchy, [report],
            references, self.subject_vectors({"Edible fats": [1, 0, 0]}), history=history)
        self.assertEqual(pairs, [])
        self.assertEqual(resolution["alias_inspections_by_query"]["S0000"], 32)
        self.assertEqual(resolution["unresolved_guides"][0]["reason"], "alias_limit")

    def test_vector_fallback_skips_receipted_unchanged_comparisons(self):
        from sse_multivector.parent_guide_workflow import resolve_vector_guides
        guides = self.guide_report({"S0000": ["Edible fats"]})
        cases, _, _ = self.prepare_comparisons(self.guide_report({"S0000": ["Dairy products"]}))
        for case in cases:
            case.update(status="valid", receipt=dict(results_path="fixture"), parsed=dict(comparisons=[
                dict(id=p["id"], relation="b_parent_of_a", reason="Broader subject.")
                for p in case["evidence"]["pairs"]]))
        previous = dict(adapter="bounded_parent_comparisons", prompt_id="BCPv5", cases=cases)
        references = {name: self.refs[name] for name in ("inputs", "hierarchy")}
        pairs, _, resolution = resolve_vector_guides(self.inputs, self.hierarchy, [guides],
            references, self.subject_vectors({"Edible fats": [1, 0, 0]}), prior_reports=[previous])
        self.assertEqual([(p["A"], p["B"]) for p in pairs], [("S0000", "S0002")])
        self.assertEqual(resolution["guides"][0]["skipped_nodes"],
                         [dict(id="S0001", reason="unchanged_judgment")])

    def test_vector_adapter_rejects_mismatched_encoder_before_packing(self):
        from sse_multivector import subject_matching_probe
        from sse_multivector import parent_guide_workflow
        report = self.guide_report({"S0000": ["Edible fats"]})
        vectors = self.subject_vectors({"Edible fats": [1, 0, 0]})
        with patch.object(subject_matching_probe, "load_subject_vectors", side_effect=[
                (vectors, dict(checkpoint_sha256="first"), {}),
                (vectors, dict(checkpoint_sha256="different"), {})]), patch.object(
                parent_guide_workflow.bounded, "_pack_comparisons") as packer:
            with self.assertRaisesRegex(ValueError, "SSE identity mismatch.*checkpoint"):
                self.prepare_comparisons(report, resolution="subject_vector_fallback_only",
                                         subject_probe="saved-subjects", guide_probe="new-guides")
            packer.assert_not_called()

    def test_vector_fallback_excludes_an_exact_pair_nominated_in_reverse(self):
        from sse_multivector.parent_guide_workflow import resolve_vector_guides
        report = self.guide_report({"S0000": ["Edible fats"], "S0001": ["Butter"]})
        references = {name: self.refs[name] for name in ("inputs", "hierarchy")}
        pairs, _, resolution = resolve_vector_guides(self.inputs, self.hierarchy, [report],
            references, self.subject_vectors({"Edible fats": [1, 0, 0]}))
        self.assertEqual([(p["A"], p["B"]) for p in pairs], [("S0000", "S0002")])
        self.assertEqual(resolution["exact_pairs_excluded_from_trial"], ["S0000-S0001"])
        self.assertEqual(resolution["guides"][0]["skipped_nodes"],
                         [dict(id="S0001", reason="exact_pair_already_selected")])


if __name__ == "__main__":
    unittest.main()
