"""Offline capacity certificates exercise the production comparison packer."""

import json
from itertools import combinations
from pathlib import Path
import unittest

from sse_multivector import bounded_hierarchy_sizing as sizing
from sse_multivector import bounded_hierarchy_workflow as workflow


class ComparisonCapacityTests(unittest.TestCase):
    def setUp(self):
        self.template = (Path(__file__).parent / "bounded-hierarchy-v1" / "BCPv5.md").read_text()

    def nodes(self, count, repetitions=8):
        return {f"S{i:04d}": [dict(index=i, subject=f"Subject {i}",
            context=("A saved context describes café, tea, and 'examples'. " *
                     (repetitions + i % 5)).rstrip())] for i in range(count)}

    def production_cases(self, nodes, pairs):
        records = []
        for a, b in pairs:
            a, b = sorted((a, b))
            records.append(dict(id=a + "-" + b, A=a, B=b))
        return workflow._pack_comparisons(records, nodes, self.template, {})

    def test_bound_covers_production_batches_and_guarantees_minimum_occupancy(self):
        nodes = self.nodes(80)
        pairs = [(f"S{i:04d}", f"S{i+1:04d}") for i in range(0, 80, 2)]
        before = json.dumps(nodes, sort_keys=True)
        result = sizing.comparison_capacity_bound(nodes, self.template, iter(pairs))
        capacity = result["guaranteed_pairs_per_request"]
        self.assertGreater(capacity, 0)
        self.assertLessEqual(capacity, workflow.MAX_PAIRS)
        self.assertLessEqual(result["max_rendered_tokens_bound"], workflow.MAX_INPUT_TOKENS)
        for start in range(len(pairs) - capacity + 1):
            packed = self.production_cases(nodes, pairs[start:start + capacity])
            self.assertEqual(len(packed), 1)
            self.assertLessEqual(packed[0]["evidence"]["input_tokens"],
                                 result["max_rendered_tokens_bound"])
        cases = self.production_cases(nodes, pairs)
        self.assertTrue(all(len(c["evidence"]["pairs"]) >= capacity for c in cases[:-1]))
        self.assertEqual(json.dumps(nodes, sort_keys=True), before)

    def test_candidate_universe_excludes_unused_large_evidence(self):
        nodes = self.nodes(6, repetitions=1)
        nodes["S0005"][0]["context"] = "Unrelated long evidence. " * 5000
        pairs = [("S0000", "S0001"), ("S0002", "S0003")]
        result = sizing.comparison_capacity_bound(nodes, self.template, pairs)
        self.assertEqual(result["guaranteed_pairs_per_request"], workflow.MAX_PAIRS)
        self.assertEqual(result["proof"]["eligible_nodes"], 4)
        self.assertEqual(result["proof"]["candidate_pairs"], 2)
        self.assertEqual(len(self.production_cases(nodes, pairs)), 1)

    def test_two_entry_unicode_and_escaped_evidence_matches_each_capacity_certificate(self):
        endings = ['Plain ending', 'Quote: "', "Thai ชา ☕", "Line\nending!", "Slash \\."]
        nodes = self.nodes(len(endings), repetitions=1)
        for i, ending in enumerate(endings):
            nodes[f"S{i:04d}"][0]["context"] = ending
            nodes[f"S{i:04d}"].append(dict(index=i + 100, subject=f"Other wording {i}",
                                           context=ending + " corroborates."))
        pairs = [(a, b) for a, b in combinations(nodes, 2)]
        result = sizing.comparison_capacity_bound(nodes, self.template, pairs)
        for k in range(1, 4):
            upper = result["proof"]["capacities"][k - 1]["rendered_tokens_upper"]
            for selected in combinations(pairs, k):
                packed = self.production_cases(nodes, selected)
                self.assertEqual(len(packed), 1)
                self.assertLessEqual(packed[0]["evidence"]["input_tokens"], upper)

    def test_empty_universe_is_vacuous_and_source_and_iteration_are_bounded(self):
        nodes = self.nodes(2, repetitions=1)
        result = sizing.comparison_capacity_bound(nodes, self.template, [])
        self.assertEqual(result["max_rendered_tokens_bound"], 0)
        self.assertTrue(result["proof"]["empty_universe"])
        with self.assertRaisesRegex(ValueError, "5000"):
            sizing.comparison_capacity_bound(self.nodes(5001, repetitions=1), self.template, [])
        with self.assertRaisesRegex(ValueError, "100000"):
            sizing.comparison_capacity_bound(nodes, self.template,
                                             (("S0000", "S0001") for _ in range(100001)))

    def test_bound_changes_with_template_and_does_not_certify_oversized_pair(self):
        nodes = self.nodes(2, repetitions=1)
        pairs = [("S0000", "S0001")]
        ordinary = sizing.comparison_capacity_bound(nodes, self.template, pairs)
        long_template = "Extra comparison instruction. " * 5000 + self.template
        oversized = sizing.comparison_capacity_bound(nodes, long_template, pairs)
        self.assertGreater(ordinary["guaranteed_pairs_per_request"], 0)
        self.assertEqual(oversized["guaranteed_pairs_per_request"], 0)
        with self.assertRaisesRegex(ValueError, "single comparison exceeds"):
            workflow._pack_comparisons([dict(id="S0000-S0001", A="S0000", B="S0001")],
                                      nodes, long_template, {})

    def test_malformed_universe_and_multiple_payload_slots_are_rejected(self):
        nodes = self.nodes(2, repetitions=1)
        for pairs in [[("S0000", "S0000")], [("S0000", "S9999")], [("S0000",)]]:
            with self.subTest(pairs=pairs), self.assertRaises(ValueError):
                sizing.comparison_capacity_bound(nodes, self.template, pairs)
        with self.assertRaises(ValueError):
            sizing.comparison_capacity_bound(nodes, self.template + "{INPUT_JSON}",
                                             [("S0000", "S0001")])


if __name__ == "__main__":
    unittest.main()
