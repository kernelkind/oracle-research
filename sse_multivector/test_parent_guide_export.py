"""Aggregate exports exercise the real shared receipt and graph codepaths."""

from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from sse_multivector import bounded_hierarchy_build as build_workflow
from sse_multivector import experiment as workflow
from sse_multivector import experiment_inputs as adapters
from sse_multivector import extraction_pipeline as engine
from sse_multivector import parent_guide_workflow as guide_workflow
from sse_multivector.bounded_hierarchy_graph import apply_relations
from sse_multivector.bounded_hierarchy_workflow import COMPARISON_SCHEMA, extract_comparisons
from sse_multivector.parent_guide_measurement import PARENT_GUIDE_SCHEMA
from sse_multivector.parent_guide_export import export_parent_guides
from sse_multivector.test_extraction_pipeline import FAKE_RUNNER


class ParentGuideExportTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / "source"
        self.source.mkdir()
        names = ["Parent A", "Child", "Parent B", "Forbidden", "Unrelated", "Alias child"]
        masks = [dict(vector_id=f"v{i}", short_id=f"V{i}", note_id="post",
                      note_short_id="N001", byte_spans=[[0, 1]], fragments=["x"])
                 for i in range(len(names))]
        self.inputs = dict(posts=[dict(note_id="post", note_short_id="N001", text="x")],
            subjects=[dict(index=i, subject=name, context=f"The original subject is {name}.",
                note_id="post", note_short_id="N001", number=str(i + 1),
                mask_vector_ids=[f"v{i}"], byte_spans=[[0, 1]], fragments=["x"])
                for i, name in enumerate(names)], edges=[[0, 1]])
        self.input_path = self.write("inputs.json", self.inputs)
        self.hierarchy = dict(experiment_id="saved-baseline", groups=[[i] for i in range(6)],
                              member_to_group=list(range(6)), edges=[[0, 1], [2, 1]])
        self.hierarchy_path = self.write("hierarchy.json", self.hierarchy)
        self.write("source/masked-posts.json", dict(notes=self.inputs["posts"]))
        self.write("source/vector-map.json", dict(vectors=masks))
        self.runner = self.root / "runner"
        self.runner.write_text(FAKE_RUNNER.replace('if prompt.startswith("GENERIC PROMPT"):', 'if True:'))
        self.runner.chmod(0o755)
        self.runner_settings = dict(runner_binary=str(self.runner), provider="openai-codex",
            model="gpt-6.1-sol", reasoning_effort="low", concurrency=1, timeout_seconds=600)
        self.templates = Path(__file__).parent / "bounded-hierarchy-v1"
        (self.root / "history").mkdir()
        self.calls = self.root / "calls.json"
        self.environment = patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.calls))
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.directory = self.root / "build"
        self.directory.mkdir()
        self.write("build/budget.json", dict(schema_version=1, limit=2000, used=17))
        historical = self.comparison_experiment("historical", {"S0001": ["Forbidden"]},
                                               {"S0001-S0003": "neither"})
        historical_report = workflow.report(historical)
        old = self.extracted(historical_report)
        application = apply_relations(self.inputs, self.hierarchy, old, work_budget=20000)
        spec = dict(inputs=str(self.input_path), hierarchy=str(self.hierarchy_path),
                    source=str(self.source), runner=self.runner_settings,
                    max_model_calls=2000, work_budget=20000)
        protected = {str(path): engine._sha256_file(path) for path in (
            self.input_path, self.hierarchy_path, self.source / "masked-posts.json",
            self.source / "vector-map.json")}
        self.plan = dict(schema_version=1, id="HG100-SOL01", policy_version="bounded-hierarchy-v1",
            spec=spec, protected_sha256=protected, code_sha256={"historical-code.py": "old-code"},
            status="finished", stop_reason="pass_limit", passes=[], comparisons=old,
            current_hierarchy=str(self.hierarchy_path), application=application, exports=[], export=None)
        build_workflow._export(self.directory, self.plan, "final-004")
        build_workflow._save(self.directory, self.plan)
        self.frozen_hierarchy = Path(self.plan["current_hierarchy"])
        self.output = self.root / "aggregate"

    def write(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))
        return path

    def extracted(self, report):
        result = []
        for case in report["cases"]:
            for row in extract_comparisons(case, case["parsed"]):
                row.update(receipt=case["receipt"], experiment=report["experiment"],
                           settings=report["settings"], prompt_id=report["prompt_id"])
                result.append(row)
        return result

    def comparison_experiment(self, name, proposals, relations, *, run=True,
                              inputs=None, hierarchy=None, changed_evidence=False, reverse=False):
        inputs = inputs or self.input_path
        hierarchy = hierarchy or getattr(self, "frozen_hierarchy", self.hierarchy_path)
        refs = dict(schema_version=1, inputs=str(inputs), hierarchy=str(hierarchy))
        guide_source = self.write(name + "-guide-source.json", dict(refs, query_nodes=list(proposals)))
        guide_spec = self.write(name + "-guide-spec.json", dict(schema_version=1,
            prompt=dict(id="PCPv3", path=str(self.templates / "PCPv3.md")),
            dataset=dict(adapter="bounded_parent_guides", path=str(guide_source)),
            runner=dict(self.runner_settings, output_schema=PARENT_GUIDE_SCHEMA)))
        guides = self.root / (name + "-guides")
        workflow.prepare(workflow.parser().parse_args(["prepare", str(guides), "--spec",
            str(guide_spec), "--history-root", str(self.root / "history")]))
        answer = dict(queries=[dict(id=q, parents=proposals[q]) for q in sorted(proposals)])
        with patch.dict(os.environ, FAKE_RUNNER_PROMPT_RESPONSE=json.dumps(answer)):
            workflow.run(guides)
        comparison_source = self.write(name + "-comparison-source.json", dict(refs, discoveries=[str(guides)]))
        comparison_spec = self.write(name + "-comparison-spec.json", dict(schema_version=1,
            prompt=dict(id="BCPv5", path=str(self.templates / "BCPv5.md")),
            dataset=dict(adapter="bounded_parent_comparisons", path=str(comparison_source)),
            runner=dict(self.runner_settings, output_schema=COMPARISON_SCHEMA)))
        comparisons = self.root / (name + "-comparisons")
        arguments = workflow.parser().parse_args(["prepare", str(comparisons), "--spec",
            str(comparison_spec), "--history-root", str(self.root / "history"), "--repeat"])
        pack = guide_workflow.bounded._pack_comparisons
        def changed(pairs, nodes, *args, **kwargs):
            pairs, nodes = deepcopy(pairs), deepcopy(nodes)
            if changed_evidence:
                nodes[pairs[0]["A"]][0]["context"] = "Not the saved original context."
                pairs[0]["reference_entries"]["A"] = nodes[pairs[0]["A"]]
            if reverse:
                for pair in pairs:
                    pair["A"], pair["B"] = pair["B"], pair["A"]
                    pair["reference_entries"] = dict(A=pair["reference_entries"]["B"],
                                                     B=pair["reference_entries"]["A"])
            return pack(pairs, nodes, *args, **kwargs)
        with patch.object(guide_workflow.bounded, "_pack_comparisons",
                          side_effect=changed if changed_evidence or reverse else pack):
            workflow.prepare(arguments)
        if run:
            answers = dict(comparisons=[dict(id=identifier, relation=relations[identifier],
                reason="saved answer") for identifier in sorted(relations)])
            with patch.dict(os.environ, FAKE_RUNNER_PROMPT_RESPONSE=json.dumps(answers)):
                workflow.run(comparisons)
        return comparisons

    def frozen_bytes(self):
        paths = [*self.directory.rglob("*"), self.input_path, self.hierarchy_path,
                 *self.source.iterdir(), self.calls]
        return {str(path): path.read_bytes() for path in paths if path.is_file()}

    def test_aggregate_keeps_source_masks_negative_judgments_and_multiple_parents(self):
        extra = self.comparison_experiment("full", {
            "S0004": ["Parent A", "Parent B"], "S0005": ["Child", "Forbidden"]}, {
            "S0000-S0004": "a_parent_of_b", "S0002-S0004": "a_parent_of_b",
            "S0001-S0005": "equivalent", "S0003-S0005": "equivalent"})
        before = self.frozen_bytes()
        summary = export_parent_guides(self.directory, [extra], self.output)
        self.assertEqual(before, self.frozen_bytes())
        self.assertEqual(summary["inference_calls"], 0)
        evidence = workflow.read(self.output / "provenance.json")
        self.assertEqual(evidence["subjects"], self.inputs["subjects"])
        self.assertEqual(evidence["original_edges"], self.inputs["edges"])
        self.assertEqual(len(evidence["masks"]), 6)
        self.assertEqual(evidence["baseline"]["comparisons"][0], self.plan["comparisons"][0])
        self.assertEqual(len(evidence["baseline"]["comparisons"]), 5)
        results = workflow.read(self.output / "results.json")
        owners = results["member_to_group"]
        self.assertEqual(owners[1], owners[5])
        self.assertNotEqual(owners[1], owners[3])
        edges = {tuple(edge) for edge in results["edges"]}
        for a, b in ((0, 1), (2, 1), (0, 4), (2, 4)):
            self.assertIn((owners[a], owners[b]), edges)
        self.assertTrue(any(row["reason"] == "neither_conflict" for row in evidence["deferred"]))

    def test_identical_receipts_are_deduplicated_without_losing_provenance(self):
        first = self.comparison_experiment("first", {"S0004": ["Parent A"]},
                                          {"S0000-S0004": "a_parent_of_b"})
        second = self.comparison_experiment("second", {"S0004": ["Parent A"]},
                                           {"S0000-S0004": "a_parent_of_b"})
        summary = export_parent_guides(self.directory, [first, second], self.output)
        evidence = workflow.read(self.output / "provenance.json")["baseline"]
        self.assertEqual(len(evidence["comparisons"]), 2)
        self.assertEqual(summary["additional_comparisons"], 1)
        self.assertEqual(len(evidence["duplicate_comparisons"]), 1)
        self.assertEqual(len(evidence["experiments"]), 2)

    def test_conflicting_duplicate_receipts_are_rejected(self):
        first = self.comparison_experiment("first", {"S0004": ["Parent A"]},
                                          {"S0000-S0004": "a_parent_of_b"})
        second = self.comparison_experiment("second", {"S0004": ["Parent A"]},
                                           {"S0000-S0004": "neither"})
        with self.assertRaisesRegex(ValueError, "conflicting"):
            export_parent_guides(self.directory, [first, second], self.output)
        self.assertFalse(self.output.exists())

    def test_unordered_duplicate_pair_direction_is_normalized(self):
        first = self.comparison_experiment("first", {"S0004": ["Parent A"]},
                                          {"S0000-S0004": "a_parent_of_b"})
        second = self.comparison_experiment("reverse", {"S0004": ["Parent A"]},
            {"S0000-S0004": "b_parent_of_a"}, reverse=True)
        summary = export_parent_guides(self.directory, [first, second], self.output)
        self.assertEqual(summary["additional_comparisons"], 1)
        self.assertEqual(summary["duplicate_comparisons"], 1)

    def test_unrun_or_malformed_comparison_reports_cannot_publish_a_final_export(self):
        for name, run, relations in (("unrun", False, {}), ("malformed", True, {})):
            extra = self.comparison_experiment(name, {"S0004": ["Parent A"]}, relations, run=run)
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "complete valid"):
                export_parent_guides(self.directory, [extra], self.output)
        self.assertFalse(self.output.exists())

    def test_foreign_source_and_changed_compact_evidence_are_rejected(self):
        foreign = self.write("foreign-inputs.json", self.inputs)
        extra = self.comparison_experiment("foreign", {"S0004": ["Parent A"]},
                                          {"S0000-S0004": "a_parent_of_b"}, inputs=foreign)
        with self.assertRaisesRegex(ValueError, "source differs"):
            export_parent_guides(self.directory, [extra], self.output)
        foreign_hierarchy = self.write("foreign-hierarchy.json", workflow.read(self.frozen_hierarchy))
        extra = self.comparison_experiment("foreign-hierarchy", {"S0004": ["Parent A"]},
            {"S0000-S0004": "a_parent_of_b"}, hierarchy=foreign_hierarchy)
        with self.assertRaisesRegex(ValueError, "source differs"):
            export_parent_guides(self.directory, [extra], self.output)
        extra = self.comparison_experiment("changed", {"S0004": ["Parent A"]},
            {"S0000-S0004": "a_parent_of_b"}, changed_evidence=True)
        with self.assertRaisesRegex(ValueError, "compact references"):
            export_parent_guides(self.directory, [extra], self.output)
        self.assertFalse(self.output.exists())

    def test_baseline_snapshot_binding_and_distinct_experiment_inputs_are_required(self):
        extra = self.comparison_experiment("extra", {"S0004": ["Parent A"]},
                                          {"S0000-S0004": "a_parent_of_b"})
        for directories in ([], [extra, extra]):
            with self.subTest(directories=directories), self.assertRaisesRegex(ValueError, "distinct"):
                export_parent_guides(self.directory, directories, self.output)
        manifest_path = Path(self.plan["export"]) / "manifest.json"
        snapshot = workflow.read(manifest_path)
        snapshot["snapshot_binding"] = "different"
        manifest_path.write_text(json.dumps(snapshot))
        with self.assertRaisesRegex(ValueError, "snapshot binding"):
            export_parent_guides(self.directory, [extra], self.output)
        self.assertFalse(self.output.exists())

    def test_source_change_during_application_is_rejected_before_publication(self):
        from sse_multivector import parent_guide_export as exporter
        extra = self.comparison_experiment("extra", {"S0004": ["Parent A"]},
                                          {"S0000-S0004": "a_parent_of_b"})
        def mutate(*args, **kwargs):
            result = apply_relations(*args, **kwargs)
            path = self.directory / "budget.json"
            path.write_text(path.read_text() + "\n")
            return result
        with patch.object(exporter, "apply_relations", side_effect=mutate):
            with self.assertRaisesRegex(ValueError, "source changed"):
                export_parent_guides(self.directory, [extra], self.output)
        self.assertFalse(self.output.exists())

    def test_build_digest_and_all_baseline_export_hashes_are_required(self):
        extra = self.comparison_experiment("extra", {"S0004": ["Parent A"]},
                                          {"S0000-S0004": "a_parent_of_b"})
        manifest_path = self.directory / build_workflow.MANIFEST
        original = manifest_path.read_bytes()
        value = workflow.read(manifest_path)
        value["sha256"] = "different"
        manifest_path.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError, "manifest hash"):
            export_parent_guides(self.directory, [extra], self.output)
        manifest_path.write_bytes(original)
        (Path(self.plan["export"]) / "categories.json").write_text("{}")
        with self.assertRaisesRegex(ValueError, "changed"):
            export_parent_guides(self.directory, [extra], self.output)
        self.assertFalse(self.output.exists())

    def test_protected_source_changes_and_output_overwrites_are_rejected(self):
        extra = self.comparison_experiment("extra", {"S0004": ["Parent A"]},
                                          {"S0000-S0004": "a_parent_of_b"})
        self.output.mkdir()
        with self.assertRaisesRegex(ValueError, "already exists"):
            export_parent_guides(self.directory, [extra], self.output)
        self.output.rmdir()
        self.input_path.write_text(self.input_path.read_text() + "\n")
        with self.assertRaisesRegex(ValueError, "source changed"):
            export_parent_guides(self.directory, [extra], self.output)
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
