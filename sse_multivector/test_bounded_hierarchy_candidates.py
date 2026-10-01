"""Production-path tests for bounded hierarchy discovery inputs."""

import hashlib
import importlib.util
import json
import math
import unittest


class CompactEntriesTests(unittest.TestCase):
    def test_second_reference_prefers_a_different_wording(self):
        from sse_multivector.bounded_hierarchy_candidates import compact_entries

        inputs = {"subjects": [
            {"index": 0, "subject": "Food", "context": "Dinner."},
            {"index": 1, "subject": "Food", "context": "Lunch."},
            {"index": 2, "subject": "Food and drink", "context": "A meal."},
        ]}
        self.assertEqual(compact_entries(inputs, [2, 1, 0]), [
            {"index": 0, "subject": "Food", "context": "Dinner."},
            {"index": 2, "subject": "Food and drink", "context": "A meal."},
        ])

    def test_context_fallback_and_identical_entries(self):
        from sse_multivector.bounded_hierarchy_candidates import compact_entries

        inputs = {"subjects": [
            {"index": 0, "subject": "Food", "context": "Dinner."},
            {"index": 1, "subject": "Food", "context": "Dinner."},
            {"index": 2, "subject": "Food", "context": "Lunch."},
        ]}
        self.assertEqual([e["index"] for e in compact_entries(inputs, [0, 1, 2])], [0, 2])
        self.assertEqual([e["index"] for e in compact_entries(inputs, [0, 1])], [0])

    def test_invalid_original_indices_are_rejected(self):
        from sse_multivector.bounded_hierarchy_candidates import compact_entries

        inputs = {"subjects": [{"index": 0, "subject": "Food", "context": "Dinner."}]}
        for members in [[], [True], [-1], [1], ["0"]]:
            with self.subTest(members=members), self.assertRaises(ValueError):
                compact_entries(inputs, members)


class DiscoveryTests(unittest.TestCase):
    def fixture(self):
        subjects = [
            ("Potatoes", "Potatoes were served.", "N001", (1.0, 0.0)),
            ("Purple potatoes", "Purple potatoes were served.", "N001", (1.0, 0.1)),
            ("Food", "Dinner was prepared.", "N002", (0.0, 1.0)),
            ("Potatoes for dinner", "Potatoes formed dinner.", "N002", (1.0, 0.01)),
        ]
        inputs = {"subjects": [], "edges": [[0, 1], [2, 3]]}
        vectors = {}
        for i, (wording, context, post, vector) in enumerate(subjects):
            digest = hashlib.sha256(wording.encode()).hexdigest()
            inputs["subjects"].append(dict(index=i, subject=wording, context=context,
                note_id=post, note_short_id=post, encoding_id=digest[:16]))
            vectors[digest, digest[:16]] = vector
        hierarchy = {"groups": [[0], [1], [2], [3]], "edges": [[0, 1], [2, 3]]}
        return inputs, hierarchy, vectors

    def test_cli_bare_import_prepares_an_empty_followup(self):
        from pathlib import Path
        import subprocess
        import sys

        code = """
from bounded_hierarchy_candidates import build_discovery
inputs = {"subjects": [{"index": 0, "subject": "Food", "context": "Dinner.",
                       "note_id": "N001", "note_short_id": "N001"}], "edges": []}
result = build_discovery(inputs, {"groups": [[0]], "edges": []}, {},
                         "Compare {INPUT_JSON}", query_nodes=[])
assert result["cases"] == []
"""
        completed = subprocess.run([sys.executable, "-c", code],
            cwd=Path(__file__).resolve().parent, capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_subject_neighbor_nominates_its_original_sp_parent(self):
        from sse_multivector.bounded_hierarchy_candidates import build_discovery

        inputs, hierarchy, vectors = self.fixture()
        result = build_discovery(inputs, hierarchy, vectors, "Compare {INPUT_JSON}",
                                 query_nodes=["S0000"])
        self.assertEqual(len(result["cases"]), 1)
        case = result["cases"][0]
        self.assertEqual(case["id"], "PCPv2-N001-001")
        payload = json.loads(case["inputs"]["INPUT_JSON"])
        self.assertEqual(payload["queries"][0]["id"], "S0000")
        self.assertIn("S0002", [node["id"] for node in payload["candidates"]])
        self.assertNotIn("context", payload["candidates"][0])
        self.assertNotIn("S0001", case["evidence"]["candidates"])

    def test_verified_current_parent_links_help_followup_retrieval(self):
        from sse_multivector.bounded_hierarchy_candidates import build_discovery

        inputs, hierarchy, vectors = self.fixture()
        word = "Things"
        digest = hashlib.sha256(word.encode()).hexdigest()
        inputs["subjects"].append(dict(index=4, subject=word, context="Things were described.",
            note_id="N003", note_short_id="N003", encoding_id=digest[:16]))
        vectors[digest, digest[:16]] = (-1.0, 0.0)
        hierarchy["groups"].append([4])
        hierarchy["edges"].append([4, 2])
        result = build_discovery(inputs, hierarchy, vectors, "Compare {INPUT_JSON}",
                                 query_nodes=["S0000"])
        self.assertIn("S0004", result["cases"][0]["evidence"]["candidates"])

    def test_exact_reference_refuses_large_corpora_before_vector_loading(self):
        from sse_multivector.bounded_hierarchy_candidates import ExactSubjectNeighbors

        inputs = {"subjects": [{"subject": f"Subject {i}"} for i in range(5001)]}
        hierarchy = {"groups": [[i] for i in range(5001)]}
        with self.assertRaisesRegex(ValueError, "5000.*ANN"):
            ExactSubjectNeighbors(inputs, hierarchy, {})

    @unittest.skipUnless(importlib.util.find_spec("hnswlib"), "hnswlib is optional")
    def test_hnsw_backend_matches_small_reference_and_builds_discovery(self):
        from sse_multivector.bounded_hierarchy_candidates import (
            ExactSubjectNeighbors, HNSWSubjectNeighbors, build_discovery)

        inputs, hierarchy, vectors = self.fixture()
        exact = ExactSubjectNeighbors(inputs, hierarchy, vectors, block_size=1)
        first = HNSWSubjectNeighbors(inputs, hierarchy, vectors)
        second = HNSWSubjectNeighbors(inputs, hierarchy, vectors)
        excluded = {"S0000", "S0001"}
        self.assertEqual(first.nearest("Potatoes", excluded),
                         exact.nearest("Potatoes", excluded))
        self.assertEqual(second.nearest("Potatoes", excluded),
                         first.nearest("Potatoes", excluded))
        result = build_discovery(inputs, hierarchy, vectors, "Compare {INPUT_JSON}",
            query_nodes=["S0000"], nearest_neighbors=first)
        self.assertIn("S0002", result["cases"][0]["evidence"]["candidates"])
        metadata = result["provenance"]["nearest_neighbors"]
        self.assertEqual(metadata["backend"], "hnsw")
        self.assertEqual(metadata["random_seed"], 17)
        self.assertEqual(metadata["inspection_limit"], 256)

    @unittest.skipUnless(importlib.util.find_spec("hnswlib"), "hnswlib is optional")
    def test_hnsw_does_not_exhaustively_search_past_inspection_limit(self):
        from sse_multivector.bounded_hierarchy_candidates import (
            ExactSubjectNeighbors, HNSWSubjectNeighbors)

        inputs, vectors = {"subjects": []}, {}
        for i in range(300):
            word = f"Word {i:04d}"
            digest = hashlib.sha256(word.encode()).hexdigest()
            inputs["subjects"].append(dict(subject=word))
            vectors[digest, digest[:16]] = math.cos(i / 1000), math.sin(i / 1000)
        hierarchy = {"groups": [[i] for i in range(300)]}
        excluded = {f"S{i:04d}" for i in range(256)}
        approximate = HNSWSubjectNeighbors(inputs, hierarchy, vectors)
        reference = ExactSubjectNeighbors(inputs, hierarchy, vectors)
        self.assertIsNone(approximate.nearest("Word 0000", excluded))
        self.assertEqual(reference.nearest("Word 0000", excluded)[0], "S0256")

    def test_current_parent_traversal_is_bounded_in_width_and_total_work(self):
        from sse_multivector.bounded_hierarchy_candidates import build_discovery

        inputs, vectors = {"subjects": [], "edges": []}, {}
        for i in range(13):
            word = "Query" if i == 0 else f"Subject {i}"
            digest = hashlib.sha256(word.encode()).hexdigest()
            inputs["subjects"].append(dict(index=i, subject=word, context=f"Context {i}",
                note_id="N001" if i == 0 else "N002",
                note_short_id="N001" if i == 0 else "N002"))
            vectors[digest, digest[:16]] = ((1.0, 0.0) if i == 0 else
                                           (1.0, 0.01) if i == 12 else (-1.0, 0.0))
        edges = [[2, 3], [8, 3], [9, 3], [10, 4], [11, 4], [6, 5], [7, 5],
                 [3, 12], [4, 12], [5, 12], [6, 12], [7, 12]]
        inputs["edges"] = edges
        hierarchy = {"groups": [[i] for i in range(13)], "edges": edges}
        result = build_discovery(inputs, hierarchy, vectors, "Compare {INPUT_JSON}",
                                 query_nodes=["S0000"])
        visited = result["provenance"]["retrieval"]["N001"][0]["visited"]
        self.assertEqual(len(visited), 8)
        self.assertLessEqual(max(e["ancestor_distance"] for e in visited), 2)
        self.assertEqual([e["node_id"] for e in visited if e["ancestor_distance"] == 1],
                         ["S0003", "S0004", "S0005"])

    def test_candidate_cap_precedes_ancestry_walks_and_direct_sp_edges_need_none(self):
        from unittest.mock import patch
        from sse_multivector import bounded_hierarchy_candidates as selection

        inputs, hierarchy, vectors = self.fixture()
        with patch.object(selection, "_ancestor", wraps=selection._ancestor) as walk:
            result = selection.build_discovery(inputs, hierarchy, vectors,
                "Compare {INPUT_JSON}", query_nodes=["S0000"], max_candidates=1)
        self.assertEqual(result["cases"][0]["evidence"]["candidates"], ["S0003"])
        self.assertEqual(walk.call_count, 2)

    def test_reachability_counts_wide_adjacency_and_fails_closed(self):
        from sse_multivector.bounded_hierarchy_candidates import _ancestor

        parents = {"query": set(), "wide": {f"S{i:04d}" for i in range(3000)}}
        parents.update({f"S{i:04d}": set() for i in range(3000)})
        self.assertIsNone(_ancestor("query", "wide", parents, max_operations=2048))
        self.assertFalse(_ancestor("query", "wide", parents, max_operations=7000))

    def test_unknown_ancestry_excludes_candidates_with_explicit_provenance(self):
        from sse_multivector.bounded_hierarchy_candidates import build_discovery

        inputs = {"subjects": [], "edges": []}
        for i in range(1200):
            inputs["subjects"].append(dict(index=i, subject=f"Subject {i}",
                context=f"Context {i}", note_id="N001" if i == 0 else "N002",
                note_short_id="N001" if i == 0 else "N002"))
        hierarchy = {"groups": [[i] for i in range(1200)],
                     "edges": [[i, i + 1] for i in range(1, 1199)]}

        class SavedNeighbor:
            metadata = {"backend": "saved-reference"}
            def nearest(self, wording, excluded):
                return "S1199", 1.0

        result = build_discovery(inputs, hierarchy, {}, "Compare {INPUT_JSON}",
            query_nodes=["S0000"], nearest_neighbors=SavedNeighbor())
        self.assertEqual(result["cases"][0]["evidence"]["candidates"], [])
        deferred = result["provenance"]["reachability_deferred"]
        self.assertEqual({record["candidate"] for record in deferred},
                         {"S1197", "S1198", "S1199"})
        self.assertTrue(all(record["query"] == "S0000" and
                            record["max_operations"] == 2048 for record in deferred))

    def test_transitive_sp_validation_fails_closed_at_its_work_limit(self):
        from sse_multivector.bounded_hierarchy_candidates import build_discovery

        size = 10002
        inputs = {"subjects": [dict(index=i, subject=f"Subject {i}",
            context=f"Context {i}", note_id="N001", note_short_id="N001")
            for i in range(size)], "edges": [[0, size - 1]]}
        hierarchy = {"groups": [[i] for i in range(size)],
                     "edges": [[i, i + 1] for i in range(size - 1)]}
        with self.assertRaisesRegex(ValueError, "SP ancestry validation exceeds"):
            build_discovery(inputs, hierarchy, {}, "Compare {INPUT_JSON}", query_nodes=[])

    def test_queries_are_owned_once_and_actual_template_tokens_are_counted(self):
        import tiktoken
        from sse_multivector.bounded_hierarchy_candidates import build_discovery
        from sse_multivector.experiment_inputs import render

        inputs, hierarchy, vectors = self.fixture()
        template = "Literal JSON: {\"answer\": []}\nCompare {INPUT_JSON}"
        result = build_discovery(inputs, hierarchy, vectors, template, max_queries=1)
        queried = [q for c in result["cases"] for q in c["evidence"]["queries"]]
        self.assertEqual(sorted(queried), ["S0000", "S0001", "S0002", "S0003"])
        self.assertEqual(len(set(queried)), len(queried))
        encoding = tiktoken.get_encoding("o200k_base")
        for case in result["cases"]:
            self.assertEqual(case["evidence"]["input_tokens"],
                             len(encoding.encode(render(template, case["inputs"]))))
        self.assertEqual(result, build_discovery(inputs, hierarchy, vectors, template,
                                                 max_queries=1))

    def test_oversized_fixed_request_fails_without_dropping_candidates(self):
        from sse_multivector.bounded_hierarchy_candidates import build_discovery

        inputs, hierarchy, vectors = self.fixture()
        with self.assertRaisesRegex(ValueError, "fixed candidate catalogue exceed"):
            build_discovery(inputs, hierarchy, vectors, "Compare {INPUT_JSON}",
                            query_nodes=["S0000"], max_input_tokens=10)

    def test_judged_original_ids_map_to_current_nodes_after_a_merge(self):
        from sse_multivector.bounded_hierarchy_candidates import build_discovery

        inputs, _, vectors = self.fixture()
        hierarchy = {"groups": [[0], [1], [2, 3]], "edges": [[0, 1]]}
        result = build_discovery(inputs, hierarchy, vectors, "Compare {INPUT_JSON}",
            query_nodes=["S0000"], judged_pairs=[("S0000", "S0003")])
        self.assertEqual(result["cases"][0]["evidence"]["candidates"], [])

    def test_current_related_nodes_and_original_sp_violations_are_rejected(self):
        from sse_multivector.bounded_hierarchy_candidates import build_discovery

        inputs, hierarchy, vectors = self.fixture()
        result = build_discovery(inputs, hierarchy, vectors, "Compare {INPUT_JSON}",
                                 query_nodes=["S0003"])
        self.assertNotIn("S0002", result["cases"][0]["evidence"]["candidates"])
        hierarchy["edges"] = [[0, 1]]
        with self.assertRaisesRegex(ValueError, "preserve original SP ancestry"):
            build_discovery(inputs, hierarchy, vectors, "Compare {INPUT_JSON}")

    def test_empty_followup_selection_creates_no_requests(self):
        from sse_multivector.bounded_hierarchy_candidates import build_discovery

        inputs, hierarchy, _ = self.fixture()
        result = build_discovery(inputs, hierarchy, {}, "Compare {INPUT_JSON}", query_nodes=[])
        self.assertEqual(result["cases"], [])
        self.assertEqual(result["stats"]["queries"], 0)


if __name__ == "__main__":
    unittest.main()
