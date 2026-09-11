"""Read-only extension checks exercise the production comparison functions."""

import copy
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from compare_hidef_resolution_extension import (
    ancestor_subgraph, compare_group_sets, group_evidence, singleton_resolution_bound,
    raw_stage_summary, validate_extension, validate_objectives,
    main,
)


class ExtensionComparisonTests(unittest.TestCase):
    @staticmethod
    def fixture():
        configuration = {
            'parameters': {'minres': .001, 'maxres': 25., 'density': .1, 'seed': 123},
            'resolutions': [.001, 25.], 'single_resolution_reference_index': 0,
            'seed_policy': 'base seed + zero-based sample index',
            'method': 'weighted', 'sources': {}, 'input_hierarchy_sha256': 'source',
            'consensus_similarity': 'strict', 'consensus_membership': 'strict',
            'containment': {}, 'dependencies': {}, 'python': '3',
            'dependency_lock_sha256': 'lock', 'graph_policy_source_sha256': 'policy',
            'input_graph': {}, 'graph': {}, 'graph_policy': {'policy': 'original'},
        }
        baseline = {
            'configuration': configuration, 'graph_bytes': b'unchanged',
            'raw': {'partitions': [
                {'sample_index': 0, 'resolution': .001, 'seed': 123, 'seconds': .5},
                {'sample_index': 1, 'resolution': 25., 'seed': 124, 'seconds': .2}],
                'reference_partition_index': 0, 'resolution_edges': [['0.0010', '25.0000']]},
            'candidates': {'groups': [{'id': 0}, {'id': 1}], 'cluster_graph_edges': [[0, 1]]},
            'hierarchy': {'sources': {}, 'canonical_unique_ids': ['a', 'b'],
                          'alias_groups': [['a'], ['b']], 'vector_count': 2,
                          'root': 2, 'method': 'weighted'},
        }
        extension = copy.deepcopy(baseline)
        extension['configuration']['parameters']['maxres'] = 190.
        extension['configuration']['resolutions'].append(190.)
        extension['raw']['partitions'].append(
            {'sample_index': 2, 'resolution': 190., 'seed': 125, 'seconds': .1})
        extension['raw']['resolution_edges'].append(['25.0000', '190.0000'])
        extension['candidates']['groups'].append({'id': 2})
        extension['candidates']['cluster_graph_edges'].append([1, 2])
        return baseline, extension

    def test_exact_old_rows_including_seconds_are_preserved_without_mutation(self):
        baseline, extension = self.fixture()
        before = copy.deepcopy((baseline, extension))
        result = validate_extension(baseline, extension)
        self.assertEqual(result['preserved_partition_count'], 2)
        self.assertEqual(result['added_partition_count'], 1)
        self.assertEqual((baseline, extension), before)
        for field, value in [('seconds', 99.), ('seed', 999), ('resolution', .002)]:
            changed = copy.deepcopy(extension)
            changed['raw']['partitions'][0][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'old raw partitions'):
                validate_extension(baseline, changed)
        changed = copy.deepcopy(extension)
        changed['candidates']['groups'][0]['extra'] = True
        with self.assertRaisesRegex(ValueError, 'old candidates'):
            validate_extension(baseline, changed)

    def test_old_edges_cannot_be_removed_or_new_old_old_edges_inserted(self):
        baseline, extension = self.fixture()
        for section, key in [('raw', 'resolution_edges'), ('candidates', 'cluster_graph_edges')]:
            changed = copy.deepcopy(extension)
            changed[section][key].pop(0)
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'old.*edges'):
                validate_extension(baseline, changed)
        baseline['raw']['resolution_edges'] = []
        with self.assertRaisesRegex(ValueError, 'old.*edges'):
            validate_extension(baseline, extension)

    def test_range_settings_graph_and_seed_changes_are_rejected(self):
        baseline, extension = self.fixture()
        changed = copy.deepcopy(extension)
        changed['configuration']['parameters']['density'] = .2
        with self.assertRaisesRegex(ValueError, 'parameters'):
            validate_extension(baseline, changed)
        changed = copy.deepcopy(extension)
        changed['graph_bytes'] = b'changed'
        with self.assertRaisesRegex(ValueError, 'graph'):
            validate_extension(baseline, changed)
        changed = copy.deepcopy(extension)
        changed['raw']['partitions'][-1]['seed'] = 123
        with self.assertRaisesRegex(ValueError, 'new partition'):
            validate_extension(baseline, changed)
        changed = copy.deepcopy(extension)
        changed['configuration']['resolutions'][-1] = 25.
        with self.assertRaisesRegex(ValueError, 'added resolutions'):
            validate_extension(baseline, changed)

    def test_set_comparison_uses_vectors_not_run_local_ids_or_note_overlap(self):
        source = [{'id': 10, 'vector_ids': [0, 1], 'note_ids': ['a', 'b']},
                  {'id': 11, 'vector_ids': [2], 'note_ids': ['a']}]
        target = [{'id': 99, 'vector_ids': [0, 1], 'note_ids': ['a', 'b']},
                  {'id': 10, 'vector_ids': [2, 3], 'note_ids': ['a', 'b']}]
        result = compare_group_sets(source, target)
        self.assertEqual(result['retained'][0]['baseline_group_id'], 10)
        self.assertEqual(result['retained'][0]['extended_group_id'], 99)
        self.assertEqual(result['lost'][0]['vector_ids'], [2])
        self.assertEqual(result['added'][0]['vector_ids'], [2, 3])

    def test_ancestry_preserves_multiple_actual_parent_routes(self):
        groups = [
            {'id': 4, 'vector_ids': [0, 1, 2, 3], 'note_ids': ['a', 'b', 'c', 'd'], 'parents': []},
            {'id': 5, 'vector_ids': [0, 1, 2], 'note_ids': ['a', 'b', 'c'], 'parents': [4]},
            {'id': 6, 'vector_ids': [0, 1, 3], 'note_ids': ['a', 'b', 'd'], 'parents': [4]},
            {'id': 7, 'vector_ids': [0, 1], 'note_ids': ['a', 'b'], 'parents': [5, 6]},
        ]
        result = ancestor_subgraph({g['id']: g for g in groups}, [7])
        self.assertEqual([g['id'] for g in result['groups']], [4, 5, 6, 7])
        self.assertEqual(result['edges'], [[4, 5], [4, 6], [5, 7], [6, 7]])

    def test_endpoint_uses_weighted_degrees_and_all_graph_edges(self):
        result = singleton_resolution_bound([(0, 1, 2.), (1, 2, 1.)], 4)
        self.assertEqual(result, 2.)

    def test_evidence_reads_saved_family_id_and_distinguishes_new_raw_support(self):
        group = {'id': 2, 'vector_ids': [0, 1], 'note_ids': ['a', 'b'], 'parents': [], 'children': []}
        raw = {'id': 8, 'vector_ids': [0, 1], 'sample_index': 3, 'resolution': 40., 'seed': 126}
        family = {'family_id': 7, 'vector_ids': [0, 1], 'support_count': 5,
                  'sample_indices': [0, 1, 2, 3, 4], 'distinct_resolution_count': 5}
        run = {'hierarchy': {'groups': [group]}, 'candidates': {'groups': [raw]},
               'persistent': {'groups': [family]}}
        evidence = group_evidence(run, group, 3)
        self.assertEqual(evidence['persistent_families'][0]['family_id'], 7)
        self.assertEqual(evidence['raw_exact_added_count'], 1)

    def test_objective_check_rejects_wrong_score_without_reoptimizing(self):
        run = {'hierarchy': {'vector_count': 3}, 'edges': [(0, 1, 2.), (1, 2, 1.)],
               'raw': {'partitions': [{'sample_index': 0, 'resolution': 1.,
                                       'membership': [0, 0, 1], 'quality': -1 / 3}]}}
        validate_objectives(run)
        run['raw']['partitions'][0]['quality'] = 0.
        with self.assertRaisesRegex(ValueError, 'objective mismatch'):
            validate_objectives(run)

    def test_raw_summary_distinguishes_repeated_singletons_and_new_multinote_sets(self):
        candidates = [
            {'sample_index': 0, 'vector_ids': [0, 1], 'note_ids': ['a', 'b']},
            {'sample_index': 1, 'vector_ids': [0], 'note_ids': ['a']},
            {'sample_index': 1, 'vector_ids': [1, 2], 'note_ids': ['b', 'c']},
            {'sample_index': 2, 'vector_ids': [0], 'note_ids': ['a']},
        ]
        result = raw_stage_summary(candidates, 1)
        self.assertEqual(result['added_candidate_count'], 3)
        self.assertEqual(result['added_singleton_candidate_count'], 2)
        self.assertEqual(result['new_unique_vector_set_count'], 2)
        self.assertEqual(result['new_unique_multinote_vector_set_count'], 1)

    def test_cli_output_is_exclusive_and_stdout_remains_the_default(self):
        result = {'validated': True}
        with tempfile.TemporaryDirectory() as temporary, patch(
                'compare_hidef_resolution_extension.compare_runs', return_value=result):
            path = Path(temporary) / 'comparison.json'
            with contextlib.redirect_stdout(io.StringIO()) as output:
                main([])
            self.assertEqual(json.loads(output.getvalue()), result)
            with contextlib.redirect_stdout(io.StringIO()) as output:
                main(['--output', str(path)])
            self.assertEqual(json.loads(path.read_text()), result)
            self.assertEqual(output.getvalue(), '')
            before = path.read_bytes()
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                main(['--output', str(path)])
            self.assertEqual(path.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
