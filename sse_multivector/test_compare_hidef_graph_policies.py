"""Small saved-artifact fixtures exercise the read-only comparison code."""

import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from compare_hidef_graph_policies import (match_groups, read_run, summarize_run,
                                         validate_replay, validate_graph_policy,
                                         validate_memberships)


class ComparisonTests(unittest.TestCase):
    def test_matches_include_hidden_groups_and_deduplicate_rankings(self):
        source = {'id': 1046, 'vector_ids': [0, 1], 'note_ids': ['a', 'b']}
        groups = [
            {'id': 10, 'vector_ids': [0, 2], 'note_ids': ['a']},
            {'id': 11, 'vector_ids': [1, 3], 'note_ids': ['b', 'c']},
            {'id': 12, 'vector_ids': [4, 5], 'note_ids': ['a', 'b']},
        ]
        matches = match_groups(source, groups)
        self.assertEqual([m['group_id'] for m in matches], [10, 11, 12])
        self.assertEqual(matches[0]['vector_jaccard'], 1 / 3)
        self.assertFalse(matches[0]['displayed'])
        self.assertEqual(matches[0]['removed_vector_ids'], [1])
        self.assertEqual(matches[0]['added_vector_ids'], [2])
        self.assertEqual(matches[2]['selected_by'], ['note_rank_1'])

    @staticmethod
    def fixture(directory):
        groups = [
            {'id': 4, 'vector_ids': [0, 1, 2, 3], 'note_ids': ['a', 'b', 'c'],
             'parents': [], 'children': [5]},
            {'id': 5, 'vector_ids': [0, 1, 2], 'note_ids': ['a', 'b'],
             'parents': [4], 'children': [6]},
            {'id': 6, 'vector_ids': [0, 2], 'note_ids': ['a', 'b'],
             'parents': [5], 'children': [7]},
            {'id': 7, 'vector_ids': [0], 'note_ids': ['a'],
             'parents': [6], 'children': []},
        ]
        files = {
            'configuration.json': {'run_id': 'fixture', 'parameters': {'seed': 123},
                                   'resolutions': [1.], 'graph': {}},
            'hierarchy.json': {'run_id': 'fixture', 'vector_count': 4, 'root': 4,
                              'canonical_unique_ids': ['v0', 'v1', 'v2', 'v3'],
                              'groups': groups},
            'raw-partitions.json': {'partitions': [{'sample_index': 0, 'resolution': 1.,
                                                   'seed': 123, 'membership': [0, 0, 0, 1],
                                                   'seconds': 1.}],
                                    'resolution_edges': [], 'reference_partition_index': 0},
            'candidates.json': {'groups': [], 'cluster_graph_edges': []},
            'persistent-groups.json': {'groups': []},
            'strict-dag.json': {'root': 4, 'groups': groups, 'edges': [
                {'parent': 4, 'child': 5}, {'parent': 5, 'child': 6}, {'parent': 6, 'child': 7}]},
            'note-projection.json': {}, 'timings.json': {},
        }
        graph = b'*Vertices 4\n0 "v0"\n1 "v1"\n2 "v2"\n3 "v3"\n*Edges\n0 2 0.9\n1 2 0.8\n'
        files['configuration.json']['graph'] = {
            'sha256': hashlib.sha256(graph).hexdigest(), 'vertices': 4, 'edges': 2,
            'weight_sum': 1.7}
        for name, value in files.items():
            (directory / name).write_text(json.dumps(value))
        (directory / 'graph.net').write_bytes(graph)
        ComparisonTests.manifest(directory)

    @staticmethod
    def manifest(directory):
        hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in directory.iterdir() if p.name != 'manifest.json'}
        (directory / 'manifest.json').write_text(json.dumps({'sha256': hashes}))

    def test_manifest_and_graph_hashes_are_checked_without_rewriting(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self.fixture(directory)
            before = {p.name: p.read_bytes() for p in directory.iterdir()}
            run = read_run(directory)
            self.assertEqual(run['edges'], [(0, 2, .9), (1, 2, .8)])
            self.assertEqual(before, {p.name: p.read_bytes() for p in directory.iterdir()})
            (directory / 'timings.json').write_text('{"changed":true}')
            with self.assertRaisesRegex(ValueError, 'manifest'):
                read_run(directory)
            self.manifest(directory)
            (directory / 'graph.net').write_bytes(before['graph.net'].replace(b'0.9', b'0.7'))
            self.manifest(directory)
            with self.assertRaisesRegex(ValueError, 'graph.*hash'):
                read_run(directory)

    def test_statistics_distinguish_note_preserving_edges_and_display_coverage(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self.fixture(directory)
            result = summarize_run(read_run(directory), ['a', 'a', 'b', 'c'])
            self.assertEqual(result['nonroot_groups'], 3)
            self.assertEqual(result['displayed_nonroot_groups'], 2)
            self.assertEqual(result['displayed_nonroot_edges'], 1)
            self.assertEqual(result['displayed_edges_same_note_set'], 1)
            self.assertEqual(result['displayed_edges_fewer_notes'], 0)
            self.assertEqual(result['isolated_vector_ids'], [3])
            self.assertEqual(result['component_sizes'], [3, 1])
            self.assertEqual(result['displayed_note_coverage']['missing_note_ids'], ['c'])

    def test_original_replay_ignores_timing_but_not_saved_memberships(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self.fixture(directory)
            reference = read_run(directory)
            replay = copy.deepcopy(reference)
            replay['hierarchy']['run_id'] = 'new-run'
            replay['raw']['partitions'][0]['seconds'] = 999.
            self.assertTrue(validate_replay(reference, replay))
            replay['raw']['partitions'][0]['membership'][0] = 1
            with self.assertRaisesRegex(ValueError, 'raw'):
                validate_replay(reference, replay)

    def test_policy_validation_checks_original_indices_and_actual_edge_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self.fixture(directory)
            original = read_run(directory)
            changed = copy.deepcopy(original)
            changed['configuration']['input_graph'] = original['configuration']['graph']
            changed['configuration']['graph_policy'] = {
                'policy': 'mutual_best_per_note', 'retained_original_edge_indices': [0],
                'removed_original_edge_indices': [1]}
            changed['graph_bytes'] = original['graph_bytes'].replace(b'1 2 0.8\n', b'')
            validate_graph_policy(changed, original, ['a', 'a', 'b', 'c'])
            changed['configuration']['graph_policy']['retained_original_edge_indices'] = [1]
            with self.assertRaises(ValueError):
                validate_graph_policy(changed, original, ['a', 'a', 'b', 'c'])

    @staticmethod
    def membership_fixture(run):
        notes = ['a', 'a', 'b', 'c']
        run['configuration'].update(parameters={'seed': 123, 'persistence': 1, 'consensus_percent': 75},
                                    resolutions=[1., 2., 3.], single_resolution_reference_index=0)
        candidates, partitions = [], []
        for index, memberships in enumerate(([0, 0, 0, 1], [0, 1, 0, 2], [0, 1, 2, 3])):
            ids = []
            for label in sorted(set(memberships)):
                vectors = [v for v, value in enumerate(memberships) if value == label]
                ids.append(len(candidates))
                candidates.append({'id': len(candidates), 'sample_index': index,
                                   'resolution': index + 1., 'seed': 123 + index,
                                   'vector_ids': vectors, 'note_ids': sorted({notes[v] for v in vectors})})
            partitions.append({'sample_index': index, 'resolution': index + 1., 'seed': 123 + index,
                               'membership': memberships, 'candidate_ids': ids})
        run['raw']['partitions'] = partitions
        run['candidates']['groups'] = candidates
        run['persistent']['groups'] = [
            {'candidate_ids': [i], 'support_count': 1, 'sample_indices': [candidates[i]['sample_index']],
             'distinct_resolution_count': 1, 'vector_ids': candidates[i]['vector_ids'],
             'note_ids': candidates[i]['note_ids']} for i in (0, 2, 5)]
        return notes

    def test_stage_validator_rejects_partition_consensus_and_dag_disagreement(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self.fixture(directory)
            valid = read_run(directory)
            notes = self.membership_fixture(valid)
            validate_memberships(valid, notes)
            changed = copy.deepcopy(valid)
            changed['raw']['partitions'][0]['membership'].pop()
            with self.assertRaisesRegex(ValueError, 'partition'):
                validate_memberships(changed, notes)
            changed = copy.deepcopy(valid)
            changed['persistent']['groups'][0]['vector_ids'] = [0, 2]
            with self.assertRaisesRegex(ValueError, 'consensus'):
                validate_memberships(changed, notes)
            changed = copy.deepcopy(valid)
            changed['hierarchy']['groups'][2]['parents'] = [4]
            with self.assertRaisesRegex(ValueError, 'DAG'):
                validate_memberships(changed, notes)

    def test_stage_validator_rejects_a_group_missing_from_persistence(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self.fixture(directory)
            run = read_run(directory)
            notes = self.membership_fixture(run)
            run['persistent']['groups'].pop()
            with self.assertRaisesRegex(ValueError, 'persistent.*DAG'):
                validate_memberships(run, notes)


if __name__ == '__main__':
    unittest.main()
