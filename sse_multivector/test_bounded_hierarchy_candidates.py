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


class DiscoveryPackingTests(unittest.TestCase):
    def fixture(self, query_count=2):
        queries = [f"S{i:04d}" for i in range(query_count)]
        references = {q: [{"index": i, "subject": q, "context": "Original context."}]
                      for i, q in enumerate(queries)}
        candidates = ["S0010", "S0011", "S0012"]
        wordings = {q: [q] for q in candidates + ["S0020", "S0021"]}
        eligible = {q: set(candidates) for q in queries}
        return queries, references, candidates, wordings, eligible

    def test_oversized_existing_catalogue_is_not_silently_recapped(self):
        from sse_multivector.bounded_hierarchy_candidates import pack_discovery_requests

        queries, references, candidates, wordings, eligible = self.fixture()
        with self.assertRaisesRegex(ValueError, "existing candidate catalogue"):
            pack_discovery_requests("N001", queries, references, candidates, wordings,
                eligible, "Compare {INPUT_JSON}",
                supplemental_by_query={"S0000": ["S0020"]}, max_candidates=2)

    def test_supplement_is_retained_and_excluded_for_other_queries(self):
        from sse_multivector.bounded_hierarchy_candidates import pack_discovery_requests

        queries = ["S0000", "S0001"]
        references = {q: [{"index": i, "subject": q, "context": "Original context."}]
                      for i, q in enumerate(queries)}
        cases = pack_discovery_requests("N001", queries, references,
            ["S0010", "S0011"], {q: [q] for q in ["S0010", "S0011", "S0020"]},
            {q: {"S0010", "S0011"} for q in queries}, "Compare {INPUT_JSON}",
            supplemental_by_query={"S0000": ["S0020"]}, max_candidates=3)
        self.assertEqual(len(cases), 1)
        self.assertEqual(cases[0]["evidence"]["candidates"], ["S0010", "S0011", "S0020"])
        self.assertEqual(cases[0]["evidence"]["excluded_candidates"],
                         {"S0001": ["S0020"]})

    def test_minimum_existing_splits_without_losing_supplements(self):
        from sse_multivector.bounded_hierarchy_candidates import pack_discovery_requests

        queries, references, candidates, wordings, eligible = self.fixture()
        cases = pack_discovery_requests("N001", queries, references, candidates,
            wordings, eligible, "Compare {INPUT_JSON}",
            supplemental_by_query={"S0000": ["S0020"], "S0001": ["S0021"]},
            minimum_existing_candidates=2, max_candidates=3)
        self.assertEqual([c["id"] for c in cases], ["PCPv2-N001-001", "PCPv2-N001-002"])
        self.assertEqual([c["evidence"]["queries"] for c in cases], [["S0000"], ["S0001"]])
        self.assertEqual([c["evidence"]["candidates"] for c in cases],
                         [["S0010", "S0011", "S0020"], ["S0010", "S0011", "S0021"]])

    def test_overlapping_supplements_are_deduplicated_before_capacity_check(self):
        from sse_multivector.bounded_hierarchy_candidates import pack_discovery_requests

        queries, references, candidates, wordings, eligible = self.fixture()
        cases = pack_discovery_requests("N001", queries, references, candidates,
            wordings, eligible, "Compare {INPUT_JSON}",
            supplemental_by_query={q: ["S0010", "S0020", "S0020"] for q in queries},
            minimum_existing_candidates=2, max_candidates=3)
        self.assertEqual(len(cases), 1)
        self.assertEqual(cases[0]["evidence"]["candidates"], ["S0010", "S0011", "S0020"])
        self.assertEqual(cases[0]["evidence"]["excluded_candidates"], {})

    def test_supplement_overlap_does_not_hide_original_query_eligibility(self):
        from sse_multivector.bounded_hierarchy_candidates import pack_discovery_requests

        queries, references, candidates, wordings, eligible = self.fixture()
        eligible["S0001"].remove("S0012")
        cases = pack_discovery_requests("N001", queries, references, candidates,
            wordings, eligible, "Compare {INPUT_JSON}",
            supplemental_by_query={"S0000": ["S0012", "S0020"]}, max_candidates=3)
        self.assertEqual(cases[0]["evidence"]["candidates"], ["S0010", "S0012", "S0020"])
        self.assertEqual(cases[0]["evidence"]["excluded_candidates"],
                         {"S0001": ["S0012", "S0020"]})

    def test_actual_tokens_split_queries_and_oversized_single_query_fails_closed(self):
        import tiktoken
        from sse_multivector.bounded_hierarchy_candidates import pack_discovery_requests
        from sse_multivector.experiment_inputs import render

        queries, references, candidates, wordings, eligible = self.fixture()
        template = 'Literal JSON: {"answers": []}\nCompare {INPUT_JSON}'
        single = pack_discovery_requests("N001", queries[:1], references, candidates,
            wordings, eligible, template, supplemental_by_query={"S0000": ["S0020"]},
            max_candidates=3)[0]
        limit = single["evidence"]["input_tokens"]
        cases = pack_discovery_requests("N001", queries, references, candidates,
            wordings, eligible, template,
            supplemental_by_query={q: ["S0020"] for q in queries},
            max_candidates=3, max_input_tokens=limit)
        self.assertEqual(len(cases), 2)
        encoding = tiktoken.get_encoding("o200k_base")
        for case in cases:
            self.assertEqual(case["evidence"]["input_tokens"],
                             len(encoding.encode(render(template, case["inputs"]))))
            self.assertIn("S0020", case["evidence"]["candidates"])
        with self.assertRaisesRegex(ValueError, "fixed candidate catalogue exceed"):
            pack_discovery_requests("N001", queries[:1], references, candidates,
                wordings, eligible, template, supplemental_by_query={"S0000": ["S0020"]},
                max_candidates=3, max_input_tokens=limit - 1)

    def test_single_query_cannot_drop_supplements_to_satisfy_minimum(self):
        from sse_multivector.bounded_hierarchy_candidates import pack_discovery_requests

        queries, references, candidates, wordings, eligible = self.fixture()
        with self.assertRaisesRegex(ValueError, "S0000.*candidate limit"):
            pack_discovery_requests("N001", queries[:1], references, candidates,
                wordings, eligible, "Compare {INPUT_JSON}",
                supplemental_by_query={"S0000": ["S0020", "S0021"]},
                minimum_existing_candidates=2, max_candidates=3)

    def test_query_limit_remains_independent_of_candidate_overlap(self):
        from sse_multivector.bounded_hierarchy_candidates import pack_discovery_requests

        queries, references, candidates, wordings, eligible = self.fixture()
        cases = pack_discovery_requests("N001", queries, references, candidates,
            wordings, eligible, "Compare {INPUT_JSON}",
            supplemental_by_query={q: ["S0020"] for q in queries},
            max_candidates=3, max_queries=1)
        self.assertEqual([c["evidence"]["queries"] for c in cases], [["S0000"], ["S0001"]])

    def test_five_supplements_per_query_are_never_dropped_at_real_request_limits(self):
        from sse_multivector.bounded_hierarchy_candidates import pack_discovery_requests

        queries = [f"S{1000 + i:04d}" for i in range(16)]
        references = {q: [{"index": i, "subject": q, "context": "Original context."}]
                      for i, q in enumerate(queries)}
        candidates = [f"S{2000 + i:04d}" for i in range(60)]
        supplements = {q: [f"S{3000 + i * 5 + j:04d}" for j in range(5)]
                       for i, q in enumerate(queries)}
        wordings = {q: [q] for q in candidates + sum(supplements.values(), [])}
        for minimum in [0, 55]:
            with self.subTest(minimum=minimum):
                cases = pack_discovery_requests("N001", queries, references, candidates,
                    wordings, {q: set(candidates) for q in queries}, "Compare {INPUT_JSON}",
                    supplemental_by_query=supplements, minimum_existing_candidates=minimum)
                self.assertEqual([q for c in cases for q in c["evidence"]["queries"]], queries)
                for case in cases:
                    evidence = case["evidence"]
                    self.assertLessEqual(len(evidence["queries"]), 16)
                    self.assertLessEqual(len(evidence["candidates"]), 60)
                    self.assertLessEqual(evidence["input_tokens"], 4000)
                    self.assertTrue(set(candidates[:minimum]) <= set(evidence["candidates"]))
                    for query in evidence["queries"]:
                        self.assertTrue(set(supplements[query]) <= set(evidence["candidates"]))
                        self.assertTrue(set(supplements[query]).isdisjoint(
                            evidence["excluded_candidates"].get(query, [])))


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

    def test_default_discovery_is_byte_for_byte_unchanged_after_packing_extraction(self):
        from sse_multivector.bounded_hierarchy_candidates import build_discovery

        inputs, hierarchy, vectors = self.fixture()
        result = build_discovery(inputs, hierarchy, vectors, "Compare {INPUT_JSON}")
        serialized = json.dumps(result, sort_keys=True, separators=(",", ":"))
        # Full production result captured before extracting its real packing path.
        self.assertEqual(hashlib.sha256(serialized.encode()).hexdigest(),
                         "dca72832d2362aca13ec8478a64e00f4998c733b14379180fed87eec676ad8d5")

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
    def test_hnsw_arbitrary_vector_returns_original_wordings_and_float64_cosines(self):
        from sse_multivector.bounded_hierarchy_candidates import HNSWSubjectNeighbors

        inputs, hierarchy, vectors = self.fixture()
        provider = HNSWSubjectNeighbors(inputs, hierarchy, vectors)
        previous = provider.nearest("Potatoes", {"S0000", "S0001"})
        query = (2.0, 3.0)
        expected = []
        for word in sorted({entry["subject"] for entry in inputs["subjects"]}):
            digest = hashlib.sha256(word.encode()).hexdigest()
            vector = vectors[digest, digest[:16]]
            score = sum(a * b for a, b in zip(vector, query)) / (
                math.hypot(*vector) * math.hypot(*query))
            expected.append((word, score))
        expected.sort(key=lambda item: (-item[1], item[0]))
        actual = provider.wording_neighbors(query)
        self.assertEqual([word for word, _ in actual], [word for word, _ in expected])
        for (_, score), (_, expected_score) in zip(actual, expected):
            self.assertIs(type(score), float)
            self.assertAlmostEqual(score, expected_score, places=14)
        self.assertEqual(provider.nearest("Potatoes", {"S0000", "S0001"}), previous)

    @unittest.skipUnless(importlib.util.find_spec("hnswlib"), "hnswlib is optional")
    def test_hnsw_arbitrary_vector_rejects_malformed_queries(self):
        from sse_multivector.bounded_hierarchy_candidates import HNSWSubjectNeighbors

        provider = HNSWSubjectNeighbors(*self.fixture())
        for vector in (None, 1.0, [], [1.0], [[1.0, 0.0]], ["bad", 1.0],
                       [math.nan, 0.0], [math.inf, 0.0], [0.0, 0.0],
                       [1e308, 1e308]):
            with self.subTest(vector=vector), self.assertRaises(ValueError):
                provider.wording_neighbors(vector)

    @unittest.skipUnless(importlib.util.find_spec("hnswlib"), "hnswlib is optional")
    def test_hnsw_arbitrary_vector_shortlist_has_stable_ties_and_bounded_wordings(self):
        from sse_multivector.bounded_hierarchy_candidates import HNSWSubjectNeighbors

        inputs, vectors = {"subjects": []}, {}
        for i in range(300):
            word = f"Word {i:04d}"
            digest = hashlib.sha256(word.encode()).hexdigest()
            inputs["subjects"].append(dict(subject=word))
            angle = 0.0 if i < 2 else i / 1000
            vectors[digest, digest[:16]] = (math.cos(angle), math.sin(angle))
        # Repeated source headings must not expand into node aliases here.
        inputs["subjects"].append(dict(subject="Word 0000"))
        hierarchy = {"groups": [[i] for i in range(len(inputs["subjects"]))]}
        first = HNSWSubjectNeighbors(inputs, hierarchy, vectors)
        second = HNSWSubjectNeighbors(inputs, hierarchy, vectors)
        actual = first.wording_neighbors((10.0, 0.0))
        self.assertEqual(len(actual), 256)
        self.assertEqual(len({word for word, _ in actual}), 256)
        self.assertEqual(actual, sorted(actual, key=lambda item: (-item[1], item[0])))
        self.assertEqual(actual[:2], [("Word 0000", 1.0), ("Word 0001", 1.0)])
        self.assertEqual(actual, first.wording_neighbors((1.0, 0.0)))
        self.assertEqual(actual, second.wording_neighbors((1.0, 0.0)))

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
