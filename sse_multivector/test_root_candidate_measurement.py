"""Offline measurement uses saved subject vectors and the real request packers."""

import hashlib
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import tempfile
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import patch


class RootCandidateTests(unittest.TestCase):
    def fixture(self):
        names = ["Beverages", "Coffee", "Morning coffee", "Preparation"]
        rows = [(1., 0.), (.99, .1), (.98, .15), (.8, .6)]
        inputs = {"subjects": [], "edges": []}
        vectors = {}
        for i, (name, row) in enumerate(zip(names, rows)):
            digest = hashlib.sha256(name.encode()).hexdigest()
            inputs["subjects"].append(dict(index=i, subject=name, context=name,
                note_id="N001", note_short_id="N001", encoding_id=digest[:16]))
            vectors[digest, digest[:16]] = row
        return inputs, {"groups": [[i] for i in range(4)], "edges": [[1, 2]]}, vectors

    def saved_build(self):
        from sse_multivector import bounded_hierarchy_build as build
        from sse_multivector.test_extraction_pipeline import FAKE_RUNNER
        from sse_multivector.test_subject_matching_probe import SavedMatchingTests

        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        source, probe = SavedMatchingTests().fixture(root)
        inputs = json.loads((probe / "inputs.json").read_text())
        for entry in inputs["subjects"]:
            entry["context"] = "Original context for " + entry["subject"]
        input_path, hierarchy_path = root / "inputs.json", root / "hierarchy.json"
        input_path.write_text(json.dumps(inputs))
        hierarchy_path.write_text(json.dumps(dict(groups=[[i] for i in range(4)],
            edges=inputs["edges"], member_to_group=list(range(4)))))
        runner = root / "runner"
        runner.write_text(FAKE_RUNNER)
        runner.chmod(0o755)
        prompts = Path(__file__).parent / "bounded-hierarchy-v1"
        spec_path = root / "spec.json"
        spec_path.write_text(json.dumps(dict(schema_version=1, id="HG100-SOL01",
            inputs=str(input_path), hierarchy=str(hierarchy_path), subject_probe=str(probe),
            source=str(source), prompts=dict(discovery=dict(id="PCPv2", path=str(prompts / "PCPv2.md")),
            comparison=dict(id="BCPv5", path=str(prompts / "BCPv5.md"))), runner=dict(
            runner_binary=str(runner), provider="openai-codex", model="gpt-6.1-sol",
            reasoning_effort="low", concurrency=1, timeout_seconds=600),
            max_model_calls=2000, max_passes=3, max_nominations_per_reference=9,
            work_budget=20000)))
        directory = root / "build"
        build.prepare_build(spec_path, directory)
        _, plan = build._load(directory)
        build._export(directory, plan, "initial-001")
        build._save(directory, plan)
        return root, directory, plan

    def test_invalid_diagnostic_ids_are_rejected_before_any_search(self):
        from sse_multivector import root_candidate_measurement as measurement

        inputs, hierarchy, vectors = self.fixture()
        for pair in [("X0000", "S0001"), ("S0000", "S0000"), ("S0000", "S9999"),
                     ("S000", "S0001"), (True, "S0001"), ("S0000",)]:
            with self.subTest(pair=pair), patch.object(measurement, "RootCandidateSearch",
                    side_effect=AssertionError("search reached")) as search:
                with self.assertRaisesRegex(ValueError, "diagnostic"):
                    measurement.measure_variants(inputs, hierarchy, vectors, [],
                        "{INPUT_JSON}", "{INPUT_JSON}", diagnostic_pairs=[pair])
                search.assert_not_called()
        hierarchy = dict(groups=[[0, 1], [2], [3]], edges=[])
        with patch.object(measurement, "RootCandidateSearch",
                          side_effect=AssertionError("search reached")) as search:
            with self.assertRaisesRegex(ValueError, "distinct current nodes"):
                measurement.measure_variants(inputs, hierarchy, vectors, [],
                    "{INPUT_JSON}", "{INPUT_JSON}", diagnostic_pairs=[("S0000", "S0001")])
            search.assert_not_called()

    def test_saved_source_size_is_checked_before_loading_vectors(self):
        from sse_multivector import bounded_hierarchy_build as build
        from sse_multivector import root_candidate_measurement as measurement

        root, directory, plan = self.saved_build()
        input_path = Path(plan["spec"]["inputs"])
        inputs = json.loads(input_path.read_text())
        inputs["subjects"] *= 1251
        input_path.write_text(json.dumps(inputs))
        plan["protected_sha256"][str(input_path)] = hashlib.sha256(input_path.read_bytes()).hexdigest()
        build._save(directory, plan)
        with patch.object(measurement, "load_subject_vectors",
                          side_effect=AssertionError("vector loading reached")) as vectors:
            with self.assertRaisesRegex(ValueError, "limited to 5000"):
                measurement.measure_build(directory, root / "measurement")
            vectors.assert_not_called()
        self.assertFalse((root / "measurement").exists())

    def test_saved_budget_must_match_frozen_policy_before_loading_vectors(self):
        from sse_multivector import root_candidate_measurement as measurement

        root, directory, _ = self.saved_build()
        for change in [dict(limit=2001), dict(schema_version=2), dict(used=-1), dict(used=True)]:
            budget = dict(schema_version=1, limit=2000, used=0)
            budget.update(change)
            (directory / "budget.json").write_text(json.dumps(budget))
            with self.subTest(change=change), patch.object(measurement, "load_subject_vectors",
                    side_effect=AssertionError("vector loading reached")) as vectors:
                with self.assertRaisesRegex(ValueError, "budget differs from frozen policy"):
                    measurement.measure_build(directory, root / "measurement")
                vectors.assert_not_called()
            self.assertFalse((root / "measurement").exists())

    def test_saved_measurement_checks_diagnostic_ids_before_loading_vectors(self):
        from sse_multivector import root_candidate_measurement as measurement

        root, directory, _ = self.saved_build()
        with patch.object(measurement, "load_subject_vectors",
                          side_effect=AssertionError("vector loading reached")) as vectors:
            with self.assertRaisesRegex(ValueError, "diagnostic"):
                measurement.measure_build(directory, root / "measurement",
                                          diagnostic_pairs=[("X0000", "S0001")])
            vectors.assert_not_called()
        self.assertFalse((root / "measurement").exists())

    def test_saved_measurement_records_current_code_and_build_plan_without_changing_sources(self):
        from sse_multivector import root_candidate_measurement as measurement

        root, directory, _ = self.saved_build()
        before = {p: p.read_bytes() for p in directory.rglob("*") if p.is_file()}
        result = measurement.measure_build(directory, root / "measurement",
                                           diagnostic_pairs=[("S0000", "S0002")])
        envelope = json.loads((directory / "bounded-build.json").read_text())
        self.assertEqual(result["source_build_plan_sha256"], envelope["sha256"])
        self.assertEqual({Path(p).name for p in result["code_sha256"]}, {
            "root_candidate_measurement.py", "bounded_hierarchy_candidates.py",
            "bounded_hierarchy_sizing.py", "bounded_hierarchy_workflow.py", "experiment.py"})
        for path, expected in result["code_sha256"].items():
            self.assertEqual(hashlib.sha256(Path(path).read_bytes()).hexdigest(), expected)
        self.assertEqual(result["existing_budget"], dict(schema_version=1, limit=2000, used=0))
        self.assertEqual(result["inference_attempts"], 0)
        self.assertTrue(result["requires_new_versioned_pass_authorization"])
        self.assertEqual(json.loads((root / "measurement" / "report.json").read_text()),
                         json.loads(json.dumps(result)))
        self.assertEqual({p: p.read_bytes() for p in before}, before)

    def test_internal_query_not_in_root_index_skips_its_existing_ancestor(self):
        from sse_multivector.root_candidate_measurement import RootCandidateSearch

        search = RootCandidateSearch(*self.fixture(), backend="exact")
        results = search.candidates("S0002", limit=1)
        self.assertEqual([r["id"] for r in results], ["S0000"])
        self.assertEqual(results[0]["query_wording"], "Morning coffee")
        self.assertEqual(results[0]["candidate_wording"], "Beverages")

    def test_ann_and_exact_external_query_agree_and_respect_judged_pairs(self):
        from sse_multivector.root_candidate_measurement import RootCandidateSearch

        judged = {frozenset(("S0002", "S0000"))}
        for backend in ("hnsw", "exact"):
            search = RootCandidateSearch(*self.fixture(), backend=backend)
            results = search.candidates("S0002", limit=5, judged_pairs=judged)
            self.assertEqual([r["id"] for r in results], ["S0003"])
            self.assertEqual(search.exclusions["already_judged"], 1)

    def test_large_exact_measurement_is_refused_before_allocating_an_index(self):
        from sse_multivector.root_candidate_measurement import RootCandidateSearch

        inputs, hierarchy, vectors = self.fixture()
        inputs["subjects"] *= 1251
        with self.assertRaisesRegex(ValueError, "limited to 5000"):
            RootCandidateSearch(inputs, hierarchy, vectors, backend="exact")

    def test_shared_cli_exposes_only_offline_measurement_command(self):
        from sse_multivector.experiment import parser

        args = parser().parse_args(["measure-root-candidates", "build", "measurement",
                                  "--pair", "S0000:S0001"])
        self.assertEqual(args.command, "measure-root-candidates")
        self.assertEqual(args.pair, ["S0000:S0001"])

    def test_measurement_packs_each_source_post_without_foreign_query_supplements(self):
        from sse_multivector.root_candidate_measurement import measure_variants

        inputs, hierarchy, vectors = self.fixture()
        for i, entry in enumerate(inputs["subjects"]):
            entry["note_id"] = entry["note_short_id"] = f"N{i + 1:03d}"
        template = "Compare.\n<input>\n{INPUT_JSON}\n</input>"
        result = measure_variants(inputs, hierarchy, vectors, [], template, template,
                                  quotas=(1,), minimum_existing=(0,))
        self.assertEqual(result["profiles"][0]["status"], "measured")
        self.assertEqual(result["inference_attempts"], 0)
        self.assertLessEqual(result["profiles"][0]["catalogue_sizes"]["max"], 60)

    def test_root_only_followup_does_not_repeat_the_existing_catalogue(self):
        from sse_multivector.root_candidate_measurement import measure_variants

        inputs, hierarchy, vectors = self.fixture()
        for i, entry in enumerate(inputs["subjects"]):
            entry["note_id"] = entry["note_short_id"] = f"N{i + 1:03d}"
        template = "Compare.\n<input>\n{INPUT_JSON}\n</input>"
        result = measure_variants(inputs, hierarchy, vectors, [], template, template,
                                  quotas=(1,), minimum_existing=(0,))
        followup = next(p for p in result["profiles"] if p.get("catalogue_mode") == "root_only_followup")
        self.assertEqual(followup["status"], "measured")
        self.assertTrue(followup["existing_graph_and_answers_unchanged"])
        self.assertEqual(followup["old_candidates_displaced"], 0)
        self.assertGreater(followup["old_candidates_not_reoffered"], 0)
        self.assertEqual(followup["maximum_rendered_input_tokens_first_attempt"],
                         followup["rendered_input_tokens"]["total"] +
                         4000 * followup["maximum_verification_requests"])
        self.assertEqual(followup["maximum_rendered_input_tokens_with_one_retry"],
                         2 * followup["maximum_rendered_input_tokens_first_attempt"])
        self.assertIsNone(result["total_output_token_ceiling"])
        self.assertGreater(result["root_search"]["normalized_subject_vector_bytes"], 0)
        self.assertGreater(result["root_search"]["root_matrix_bytes"], 0)
        self.assertGreater(result["process_peak_rss_kib"], 0)

    def test_offline_cli_writes_full_report_but_prints_compact_measurements(self):
        from sse_multivector import experiment

        root, directory, _ = self.saved_build()
        destination = root / "measurement"
        output = io.StringIO()
        with redirect_stdout(output):
            experiment.main(["measure-root-candidates", str(directory), str(destination)])
        summary = json.loads(output.getvalue())
        self.assertEqual(summary["measurement_report"], str(destination / "report.json"))
        self.assertEqual(summary["inference_attempts"], 0)
        self.assertNotIn("comparison_capacity", summary["profiles"][0])
        full = json.loads((destination / "report.json").read_text())
        self.assertIn("comparison_capacity", full["profiles"][0])

    def test_root_query_scope_measures_only_the_starting_view_without_hiding_other_nodes(self):
        from sse_multivector.root_candidate_measurement import measure_variants

        inputs, hierarchy, vectors = self.fixture()
        original = json.dumps(hierarchy, sort_keys=True)
        result = measure_variants(inputs, hierarchy, vectors, [], "Compare {INPUT_JSON}",
            "Compare {INPUT_JSON}", quotas=(1,), minimum_existing=(0,),
            diagnostic_pairs=[("S0000", "S0002")])
        profile = next(p for p in result["profiles"] if p.get("query_scope") == "roots")
        self.assertEqual(profile["queried_nodes"], 3)
        self.assertEqual(profile["queries_per_request"]["total"], 3)
        self.assertEqual(result["node_count"], 4)
        self.assertEqual(json.dumps(hierarchy, sort_keys=True), original)
        internal_direction = next(d for d in profile["diagnostic_pairs"][0]["directions"]
                                  if d["query"] == "S0002")
        self.assertFalse(internal_direction["query_in_scope"])
        self.assertFalse(internal_direction["in_combined_request"])

    @unittest.skipUnless(sys.platform == "linux", "Linux exposes this process's post-exec VmHWM")
    def test_memory_measurement_excludes_inherited_pre_exec_high_water_mark(self):
        from sse_multivector import root_candidate_measurement as measurement

        inputs, hierarchy, vectors = self.fixture()
        with patch.object(measurement.resource, "getrusage",
                          return_value=SimpleNamespace(ru_maxrss=10**12)):
            result = measurement.measure_variants(inputs, hierarchy, vectors, [],
                "Compare {INPUT_JSON}", "Compare {INPUT_JSON}", quotas=(1,), minimum_existing=(0,))
        self.assertLess(result["process_peak_rss_kib"], 10**12)
        self.assertEqual(result["process_peak_rss_source"], "/proc/self/status VmHWM")


if __name__ == "__main__":
    unittest.main()
