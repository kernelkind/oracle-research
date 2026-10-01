"""Production graph application and browser export, without model requests."""

from copy import deepcopy
import json
from pathlib import Path
import random
import tempfile
import unittest

try:
    from .bounded_hierarchy_graph import apply_relations, export_hierarchy
    from .subject_hierarchy import reachable
except ImportError:
    from bounded_hierarchy_graph import apply_relations, export_hierarchy
    from subject_hierarchy import reachable


def fixture(count=4, edges=()):
    subjects = [dict(id=i, subject=f"Subject {i}", context=f"Context {i}",
                     note_id=f"post-{i}", note_short_id=f"N{i + 1:03d}",
                     number="1", mask_vector_ids=[f"V{i}"],
                     byte_spans=[[0, 4]], fragments=["text"])
                for i in range(count)]
    posts = [dict(note_id=s["note_id"], note_short_id=s["note_short_id"], text="text")
             for s in subjects]
    inputs = dict(subjects=subjects, posts=posts, edges=[list(e) for e in edges])
    hierarchy = dict(experiment_id="saved-base", groups=[[i] for i in range(count)],
                     member_to_group=list(range(count)), edges=[list(e) for e in edges],
                     sp_edges=[list(e) for e in edges])
    return inputs, hierarchy


def judgment(a, b, relation, **extra):
    return dict(id=f"S{a:04d}-S{b:04d}", A=f"S{a:04d}", B=f"S{b:04d}",
                answer=dict(relation=relation, reason="Saved test answer"),
                receipt=dict(record_sha256="fixture"), **extra)


class BoundedHierarchyGraphTests(unittest.TestCase):
    def test_neither_audit_reports_paths_sp_conflicts_and_unfinished_checks(self):
        from sse_multivector.bounded_hierarchy_graph import audit_neither
        inputs, hierarchy = fixture(edges=[(0, 1), (1, 2)])
        judgments = [judgment(0, 2, "neither"), judgment(0, 3, "neither")]
        result = apply_relations(inputs, hierarchy, judgments, freeze_membership=True,
                                 cross_pair_neither="diagnostic")
        audit = audit_neither(result, judgments, work_budget=20000)
        self.assertEqual(audit["contradictions"][0]["path"], ["S0000", "S0001", "S0002"])
        self.assertEqual(audit["compatible_pairs"], 1)
        limited = audit_neither(result, judgments, work_budget=0)
        self.assertEqual(len(limited["unresolved"]), 2)
        self.assertEqual(limited["compatible_pairs"], 0)
        self.assertEqual(result["results"]["edges"], hierarchy["edges"])

    def test_fixed_membership_remaps_historical_same_pair_disagreements(self):
        inputs, hierarchy = fixture(5)
        hierarchy.update(groups=[[0, 1], [2, 3], [4]], member_to_group=[0, 0, 1, 1, 2])
        judgments = [judgment(0, 2, "a_parent_of_b"), judgment(3, 1, "neither")]
        for policy in ("binding", "diagnostic"):
            result = apply_relations(inputs, hierarchy, judgments, freeze_membership=True,
                                     cross_pair_neither=policy)
            self.assertEqual(result["results"]["edges"], [])
            self.assertEqual([row["reason"] for row in result["deferred"]],
                             ["judgment_conflict", "judgment_conflict"])

    def test_diagnostic_policy_does_not_skip_work_limits_or_enable_merges(self):
        inputs, hierarchy = fixture(edges=[(0, 1)])
        with self.assertRaisesRegex(ValueError, "fixed membership"):
            apply_relations(inputs, hierarchy, [], cross_pair_neither="diagnostic")
        for policy in ("binding", "diagnostic"):
            result = apply_relations(inputs, hierarchy, [judgment(2, 3, "a_parent_of_b")],
                work_budget=0, freeze_membership=True, cross_pair_neither=policy)
            self.assertEqual(result["results"]["edges"], [[0, 1]])
            self.assertEqual(result["deferred"][0]["reason"], "work_budget")

    def test_fixed_membership_parent_replay_can_record_cross_pair_neither(self):
        inputs, hierarchy = fixture(edges=[(0, 1)])
        judgments = [judgment(0, 2, "neither"), judgment(1, 2, "a_parent_of_b"),
                     judgment(2, 3, "equivalent")]
        original = deepcopy((inputs, hierarchy, judgments))
        binding = apply_relations(inputs, hierarchy, judgments, freeze_membership=True)
        diagnostic = apply_relations(inputs, hierarchy, judgments, freeze_membership=True,
                                     cross_pair_neither="diagnostic")
        self.assertEqual(binding["results"]["edges"], [[0, 1]])
        self.assertEqual(diagnostic["results"]["edges"], [[0, 1], [1, 2]])
        self.assertEqual(diagnostic["results"]["groups"], hierarchy["groups"])
        self.assertTrue(any(row["reason"] == "ancestor_with_neither_conflict"
                            for row in diagnostic["applied"]))
        self.assertTrue(any(row["reason"] == "fixed_membership"
                            for row in diagnostic["deferred"]))
        self.assertEqual((inputs, hierarchy, judgments), original)

    def test_diagnostic_policy_still_defers_same_pair_conflicts_and_cycles(self):
        inputs, hierarchy = fixture(edges=[(0, 1)])
        judgments = [judgment(1, 2, "neither"), judgment(1, 2, "a_parent_of_b"),
                     judgment(0, 1, "b_parent_of_a")]
        result = apply_relations(inputs, hierarchy, judgments, freeze_membership=True,
                                 cross_pair_neither="diagnostic")
        self.assertEqual(result["results"]["edges"], [[0, 1]])
        self.assertEqual([row["reason"] for row in result["deferred"]].count("judgment_conflict"), 2)
        self.assertIn("cycle", {row["reason"] for row in result["deferred"]})
        self.assertEqual(result, apply_relations(inputs, hierarchy, list(reversed(judgments)),
                         freeze_membership=True, cross_pair_neither="diagnostic"))

    def test_equivalence_preserves_every_entry_and_internal_sp_relationship(self):
        inputs, hierarchy = fixture(edges=[(0, 1), (1, 2)])
        result = apply_relations(inputs, hierarchy, [judgment(0, 1, "equivalent")])
        self.assertEqual(result["results"]["groups"], [[0, 1], [2], [3]])
        self.assertEqual(result["mapping"]["S0001"], "S0000")
        self.assertEqual(result["results"]["edges"], [[0, 1]])
        self.assertEqual(result["stats"]["subjects"], 4)
        self.assertTrue(result["stats"]["sp_order_preserved"])

    def test_equivalence_that_creates_distinct_node_cycle_is_deferred(self):
        inputs, hierarchy = fixture(edges=[(0, 2), (2, 1)])
        result = apply_relations(inputs, hierarchy, [judgment(0, 1, "equivalent")])
        self.assertEqual(result["results"]["groups"], hierarchy["groups"])
        self.assertEqual(result["deferred"][0]["reason"], "cycle")

    def test_parent_cycle_and_transitive_neither_conflict_are_deferred(self):
        inputs, hierarchy = fixture(edges=[(0, 1)])
        judgments = [judgment(0, 2, "neither"), judgment(1, 2, "a_parent_of_b"),
                     judgment(0, 1, "b_parent_of_a")]
        result = apply_relations(inputs, hierarchy, judgments)
        self.assertEqual(result["results"]["edges"], [[0, 1]])
        self.assertEqual({d["reason"] for d in result["deferred"]},
                         {"cycle", "neither_conflict"})

    def test_equivalence_cannot_create_ancestry_for_previously_neither_nodes(self):
        inputs, hierarchy = fixture(edges=[(2, 0), (1, 3)])
        result = apply_relations(inputs, hierarchy,
                                [judgment(2, 3, "neither"), judgment(0, 1, "equivalent")])
        self.assertEqual(result["results"]["groups"], hierarchy["groups"])
        self.assertEqual(result["deferred"][0]["reason"], "neither_conflict")

    def test_unrelated_neither_history_does_not_consume_each_proposal_budget(self):
        inputs, hierarchy = fixture(40)
        judgments = [judgment(i, i + 1, "neither") for i in range(2, 38, 2)]
        judgments.append(judgment(0, 1, "a_parent_of_b"))
        result = apply_relations(inputs, hierarchy, judgments, work_budget=15)
        self.assertEqual(result["results"]["edges"], [[0, 1]])
        self.assertFalse(result["deferred"])

    def test_endpoint_index_follows_lazy_equivalence_members(self):
        inputs, hierarchy = fixture(6)
        result = apply_relations(inputs, hierarchy, [judgment(1, 5, "neither"),
            judgment(0, 1, "equivalent"), judgment(0, 4, "a_parent_of_b"),
            judgment(4, 5, "a_parent_of_b")])
        self.assertEqual(result["results"]["groups"], [[0, 1], [2], [3], [4], [5]])
        self.assertEqual(result["results"]["edges"], [[0, 3]])
        self.assertEqual(result["deferred"][0]["reason"], "neither_conflict")

    def test_equivalence_chain_cannot_collapse_explicit_strict_ancestor_answer(self):
        inputs, hierarchy = fixture()
        result = apply_relations(inputs, hierarchy, [judgment(0, 1, "equivalent"),
            judgment(1, 2, "equivalent"), judgment(0, 2, "a_parent_of_b")])
        self.assertEqual(result["results"]["groups"], [[0, 1], [2], [3]])
        self.assertEqual(result["results"]["edges"], [[0, 1]])
        self.assertEqual(result["deferred"][0]["reason"], "ancestor_conflict")

    def test_indexed_negative_checks_preserve_constraints_across_small_dags(self):
        generator = random.Random(2741)
        for trial in range(30):
            edges = [(a, b) for a in range(12) for b in range(a + 1, 12)
                     if generator.random() < 0.06]
            inputs, hierarchy = fixture(12, edges)
            source_closure = reachable(12, edges)
            negatives = [judgment(a, b, "neither") for a in range(12)
                         for b in range(a + 1, 12) if (a, b) not in source_closure
                         and generator.random() < 0.1]
            positives = []
            occupied = {(j["A"], j["B"]) for j in negatives}
            for a in range(12):
                for b in range(a + 1, 12):
                    if (f"S{a:04d}", f"S{b:04d}") not in occupied and generator.random() < 0.13:
                        positives.append(judgment(a, b, generator.choice(
                            ["equivalent", "a_parent_of_b", "b_parent_of_a"])))
            result = apply_relations(inputs, hierarchy, negatives + positives)
            closure = reachable(result["stats"]["nodes"], result["results"]["edges"])
            owners = result["results"]["member_to_group"]
            with self.subTest(trial=trial):
                for negative in negatives:
                    a, b = (owners[int(negative[key][1:])] for key in ("A", "B"))
                    self.assertNotEqual(a, b)
                    self.assertNotIn((a, b), closure)
                    self.assertNotIn((b, a), closure)

    def test_conflicting_answers_do_not_choose_a_pair_winner(self):
        inputs, hierarchy = fixture()
        result = apply_relations(inputs, hierarchy,
                                [judgment(0, 1, "equivalent"), judgment(0, 1, "neither")])
        self.assertEqual(result["results"]["groups"], hierarchy["groups"])
        self.assertEqual(len(result["deferred"]), 2)
        self.assertTrue(all(d["reason"] == "judgment_conflict" for d in result["deferred"]))

    def test_exhausted_work_budget_defers_without_dropping_sp_edges(self):
        inputs, hierarchy = fixture(edges=[(0, 1)])
        result = apply_relations(inputs, hierarchy,
                                [judgment(2, 3, "a_parent_of_b")], work_budget=0)
        self.assertEqual(result["results"]["edges"], [[0, 1]])
        self.assertEqual(result["deferred"][0]["reason"], "work_budget")

    def test_wide_adjacency_is_budgeted_before_neighbor_enumeration(self):
        inputs, hierarchy = fixture(30, edges=[(0, i) for i in range(1, 29)])
        result = apply_relations(inputs, hierarchy,
                                [judgment(0, 1, "b_parent_of_a")], work_budget=5)
        self.assertEqual(result["results"]["edges"], hierarchy["edges"])
        self.assertEqual(result["deferred"][0]["reason"], "work_budget")
        self.assertLessEqual(result["deferred"][0]["inspected"], 5)

    def test_snapshot_retains_canonical_labels_and_direct_empty_mask_posts(self):
        inputs, hierarchy = fixture(edges=[(0, 1)])
        inputs["subjects"][0].update(subject="Food", context="Food described through soup.")
        inputs["subjects"][1].update(subject="Foods", context="Foods described through bread.",
                                     mask_vector_ids=[], byte_spans=[], fragments=[])
        application = apply_relations(inputs, hierarchy, [judgment(0, 1, "equivalent")])
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            source = directory / "source"
            source.mkdir()
            (source / "masked-posts.json").write_text(json.dumps(dict(notes=inputs["posts"])))
            masks = [dict(vector_id=f"V{i}", short_id=f"M{i}",
                          **{key: s[key] for key in
                             ("note_id", "note_short_id", "byte_spans", "fragments")})
                     for i, s in enumerate(inputs["subjects"]) if s["mask_vector_ids"]]
            (source / "vector-map.json").write_text(json.dumps(dict(vectors=masks)))
            bundle = export_hierarchy(directory / "view", inputs, application, source=source)
            food = next(n for n in bundle["categories"]["nodes"] if n["node_id"] == "S0000")
            self.assertEqual(food["label"], "Food")
            self.assertEqual(food["note_ids"], ["N001", "N002"])
            self.assertIn("Foods", food["analysis"])
            self.assertEqual(bundle["categories"]["note_masks"]["S0000"]["N002"], [])

    def test_equivalences_first_and_pair_order_are_deterministic(self):
        inputs, hierarchy = fixture()
        judgments = [judgment(2, 3, "a_parent_of_b"), judgment(0, 2, "equivalent"),
                     judgment(1, 3, "a_parent_of_b")]
        result = apply_relations(inputs, hierarchy, judgments)
        reverse = apply_relations(inputs, hierarchy, list(reversed(judgments)))
        self.assertEqual(result, reverse)
        self.assertEqual(result["results"]["groups"], [[0, 2], [1], [3]])
        self.assertEqual(result["results"]["edges"], [[0, 2], [1, 2]])

    def test_inputs_and_receipts_remain_unchanged_and_unknown_nodes_fail(self):
        inputs, hierarchy = fixture()
        judgments = [judgment(0, 1, "a_parent_of_b", stage="HG7-inherited")]
        originals = deepcopy((inputs, hierarchy, judgments))
        result = apply_relations(inputs, hierarchy, judgments)
        self.assertEqual((inputs, hierarchy, judgments), originals)
        self.assertEqual(result["applied"][0]["judgment"]["stage"], "HG7-inherited")
        with self.assertRaisesRegex(ValueError, "unknown"):
            apply_relations(inputs, hierarchy, [judgment(0, 8, "equivalent")])

    def test_export_reuses_browser_and_preserves_sources_masks_and_provenance(self):
        inputs, hierarchy = fixture(edges=[(0, 1), (1, 2)])
        application = apply_relations(inputs, hierarchy,
                                      [judgment(0, 2, "a_parent_of_b")])
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            source = directory / "source"
            source.mkdir()
            (source / "masked-posts.json").write_text(json.dumps(dict(notes=inputs["posts"])))
            masks = [dict(vector_id=f"V{i}", short_id=f"M{i}",
                          **{key: s[key] for key in
                             ("note_id", "note_short_id", "byte_spans", "fragments")})
                     for i, s in enumerate(inputs["subjects"])]
            (source / "vector-map.json").write_text(json.dumps(dict(vectors=masks)))
            baseline = dict(comparisons=[dict(stage="HG7-inherited", receipt={"old": True})])
            bundle = export_hierarchy(directory / "view", inputs, application,
                                      source=source, provenance=baseline)
            result = bundle["results"]
            self.assertEqual(result["browsing_edges"], [[0, 1], [1, 2]])
            self.assertEqual(reachable(4, result["edges"]),
                             reachable(4, result["browsing_edges"]))
            self.assertEqual(len(bundle["categories"]["notes"]), 4)
            self.assertEqual(len(bundle["provenance"]["subjects"]), 4)
            self.assertEqual(len(bundle["provenance"]["masks"]), 4)
            self.assertEqual(bundle["provenance"]["baseline"], baseline)
            self.assertEqual(bundle["provenance"]["posts"], inputs["posts"])
            self.assertTrue((directory / "view" / "categories.json").is_file())
            with self.assertRaisesRegex(ValueError, "exist"):
                export_hierarchy(directory / "view", inputs, application, source=source)


if __name__ == "__main__":
    unittest.main()
