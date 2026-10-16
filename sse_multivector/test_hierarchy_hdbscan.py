"""Numerical section selection through the production HDBSCAN adapter."""

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from sse_multivector import hierarchy_hdbscan as hdbscan


def fixture(groups=7, distances=None):
    count = 2 * groups
    ids = [f"{i:064x}" for i in range(count)]
    mapping = {x: f"L{i+1:05d}" for i, x in enumerate(ids)}
    request = dict(hdbscan_configuration=hdbscan.CONFIG,
                   source_vector_manifest_sha256="a"*64,
                   normalized_vector_sha256="b"*64)
    leaves = [count+groups-1+i for i in range(groups)]
    segments = [ids[2*i:2*i+2] for i in range(groups)]
    distances = distances or [groups-i-1 for i in range(groups-1)]
    edges = []
    for i in range(groups-1):
        children = [count+i+1, leaves[groups-i-1]] if i < groups-2 else leaves[:2]
        edges.extend(dict(parent=count+i, child=c, child_size=2,
                          **{"lambda": 1/distances[i]}) for c in children)
    result = dict(canonical_unique_ids=ids, alias_groups=[[x] for x in ids],
                  fine_output=dict(segments=segments), algorithm_result=dict(
                      vector_count=count, condensed_tree=edges,
                      clusters=[dict(id=c, members=[2*i, 2*i+1])
                                for i, c in enumerate(leaves)]))
    response = dict(schema_version=1, candidate_identity="hdbscan-explicit-config-v1",
                    artifact=dict(canonical_input_ids=ids,
                                  canonical_configuration_json=json.dumps(hdbscan.CONFIG),
                                  result=result, manifest=dict(
                                      parameters=hdbscan.CONFIG,
                                      algorithm_version="hdbscan-star-exact-angular-v1",
                                      fine_output_selector_version="hdbscan-clusters-members-v1",
                                      **request)))
    return response, request, mapping


class HdbscanSectionTests(unittest.TestCase):
    def test_hierarchy_output_preserves_the_same_groups_and_section_cut(self):
        response, request, mapping = fixture(14)
        expected = hdbscan.section_plan(response, request, mapping, 6)
        response['candidate_identity'] = 'hdbscan-hierarchy-output-v1'
        self.assertEqual(hdbscan.section_plan(response, request, mapping, 6), expected)

    def test_coordinator_reuses_results_across_advances_but_not_across_runs(self):
        from sse_multivector import experiment as workflow
        response, request, mapping = fixture(7)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'result.json'
            path.write_text(json.dumps(response))
            read_bytes = Path.read_bytes
            reads = []

            def counted(source):
                reads.append(source)
                return read_bytes(source)

            with patch.object(Path, 'read_bytes', counted):
                with hdbscan.source_scope():
                    for _ in range(3):
                        with workflow.report_scope():
                            self.assertEqual(hdbscan.members(hdbscan.read_result(path), request, mapping),
                                             hdbscan.members(response, request, mapping))
                self.assertEqual(reads, [path])
                with hdbscan.source_scope():
                    hdbscan.read_result(path)
                self.assertEqual(reads, [path, path])

    def test_compact_result_preserves_every_consumed_field_and_the_raw_source(self):
        from sse_multivector import experiment as workflow
        response, request, mapping = fixture(7)
        expected = deepcopy(response)
        response['artifact']['result']['algorithm_result'].update(
            mutual_reachability_distances=[0.0] * 100, minimum_spanning_tree=[], labels=[])
        response['artifact']['canonical_fine_output_json'] = 'unused diagnostics'
        response['artifact']['result']['fine_output']['unassigned'] = []
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'result.json'
            raw = json.dumps(response).encode()
            path.write_bytes(raw)
            with workflow.report_scope() as files:
                compact = hdbscan.read_result(path)
                self.assertEqual(compact, expected)
                self.assertEqual(hdbscan.project(compact, request, mapping),
                                 hdbscan.project(response, request, mapping))
                self.assertEqual(files.sha256(path), hdbscan.trial._hash(path))
            self.assertEqual(path.read_bytes(), raw)

    def test_v42_rejects_groups_below_four_and_mismatched_controls(self):
        response, request, mapping = fixture(3)
        request["hdbscan_configuration"] = hdbscan.CONFIG_V42
        with self.assertRaisesRegex(ValueError, "controls"):
            hdbscan.members(response, request, mapping)
        response["artifact"]["canonical_configuration_json"] = json.dumps(hdbscan.CONFIG_V42)
        response["artifact"]["manifest"]["parameters"] = hdbscan.CONFIG_V42
        with self.assertRaisesRegex(ValueError, "group membership"):
            hdbscan.members(response, request, mapping)

    def test_first_six_section_cut_and_recursive_leaf_stop(self):
        response, request, mapping = fixture(14)
        plan = hdbscan.section_plan(response, request, mapping, 6)
        by_id = {s["cluster_id"]: s for s in plan["sections"]}
        self.assertEqual(len(plan["roots"]), 6)
        self.assertEqual([len(by_id[c]["original_ids"]) for c in plan["roots"]],
                         [18, 2, 2, 2, 2, 2])
        self.assertEqual(len(plan["sections"]), 16)
        self.assertEqual(len([s for s in plan["sections"] if s["group"]]), 14)
        self.assertTrue(all(len(s["children"]) <= 6 for s in plan["sections"]))
        self.assertEqual(plan["cuts"][0]["boundary"], dict(lower=8, upper=9, epsilon=8.5))

    def test_small_groups_are_shown_directly(self):
        response, request, mapping = fixture(4)
        plan = hdbscan.section_plan(response, request, mapping, 6)
        self.assertEqual(len(plan["roots"]), 4)
        self.assertEqual(len(plan["sections"]), 4)
        self.assertTrue(all(s["group"] and not s["children"] for s in plan["sections"]))

    def test_equal_distances_merge_together_and_can_yield_fewer_than_six(self):
        response, request, mapping = fixture(7, [3, 2, 2, 2, 1, 1])
        plan = hdbscan.section_plan(response, request, mapping, 6)
        self.assertEqual(len(plan["roots"]), 5)
        self.assertEqual(plan["cuts"][0]["boundary"], dict(lower=1, upper=2, epsilon=1.5))
        response, request, mapping = fixture(7, [1]*6)
        with self.assertRaisesRegex(ValueError, "tied split"):
            hdbscan.section_plan(response, request, mapping, 6)

    def test_unassigned_entries_are_not_absorbed_into_ancestor_sections(self):
        response, request, mapping = fixture(7)
        response["artifact"]["result"]["fine_output"]["segments"].pop()
        response["artifact"]["result"]["algorithm_result"]["clusters"].pop()
        plan = hdbscan.section_plan(response, request, mapping, 6)
        represented = {i for s in plan["sections"] for i in s["original_ids"]}
        self.assertEqual(represented, {f"L{i:05d}" for i in range(1, 13)})

    def test_empty_and_single_selected_group(self):
        response, request, mapping = fixture(3)
        response["artifact"]["result"]["fine_output"]["segments"] = []
        response["artifact"]["result"]["algorithm_result"]["clusters"] = []
        self.assertEqual(hdbscan.section_plan(response, request, mapping, 6),
                         dict(roots=[], sections=[], cuts=[]))
        response, request, mapping = fixture(3)
        response["artifact"]["result"]["fine_output"]["segments"] = response["artifact"]["result"]["fine_output"]["segments"][:1]
        response["artifact"]["result"]["algorithm_result"]["clusters"] = response["artifact"]["result"]["algorithm_result"]["clusters"][:1]
        plan = hdbscan.section_plan(response, request, mapping, 6)
        self.assertEqual(len(plan["sections"]), 1)
        self.assertEqual(len(plan["roots"]), 1)

    def test_vector_aliases_preserve_every_original_entry(self):
        response, request, mapping = fixture(3)
        result = response["artifact"]["result"]
        alias = "f"*64
        mapping[alias] = "L00007"
        result["alias_groups"][0].append(alias)
        result["fine_output"]["segments"][0].append(alias)
        response["artifact"]["canonical_input_ids"] = sorted(mapping)
        plan = hdbscan.section_plan(response, request, mapping, 6)
        self.assertEqual(len(plan["sections"][0]["original_ids"]), 3)

    def test_invalid_selected_membership_and_cyclic_tree_are_rejected(self):
        response, request, mapping = fixture(7)
        corrupt = deepcopy(response)
        corrupt["artifact"]["result"]["algorithm_result"]["clusters"][0]["members"] = [2, 3]
        with self.assertRaisesRegex(ValueError, "differs from saved group"):
            hdbscan.section_plan(corrupt, request, mapping, 6)
        response["artifact"]["result"]["algorithm_result"]["condensed_tree"][0]["parent"] = 15
        with self.assertRaisesRegex(ValueError, "condensed tree"):
            hdbscan.section_plan(response, request, mapping, 6)


if __name__ == "__main__":
    unittest.main()
